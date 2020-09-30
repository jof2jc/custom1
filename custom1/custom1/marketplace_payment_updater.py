# -*- coding: utf-8 -*-
# Copyright (c) 2017, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, os
from frappe import _
import frappe.modules.import_file
from frappe.model.document import Document
from frappe.utils.data import format_datetime, cstr, flt
from frappe.utils.csvutils import getlink

from frappe.utils import get_files_path
from frappe.utils.background_jobs import enqueue
import json

from pdfminer.layout import LAParams, LTTextBox
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import resolve1


@frappe.whitelist()
def upload_marketplace_payment(docname):
	frappe.db.set_value("Payment Entry", docname, "import_status", "In Progress", update_modified=False)

	frappe.publish_realtime("marketplace_payment_progress", {"progress": "0",
		"data_import": docname, "reload": True}, user=frappe.session.user)

	from frappe.core.page.background_jobs.background_jobs import get_info
	enqueued_jobs = [d.get("job_name") for d in get_info()]

	if docname not in enqueued_jobs:
		enqueue(execute_upload_marketplace_payment, queue='default', timeout=1000, event='data_import', job_name=docname,
			data_import_doc=docname, user=frappe.session.user)


def execute_upload_marketplace_payment(rows = None, submit_after_import=None, ignore_encoding_errors=False, no_email=True, overwrite=None,
	update_only = None, ignore_links=False, pre_process=None, via_console=False, from_data_import="No",
	skip_errors = True, data_import_doc=None, validate_template=False, user=None):

	rows = None
	error_flag = rollback_flag = False
	err_msg = ""
	data = data_with_error = []
	import_Status = ""
	total=1
	customer = ""

	data_import_doc = frappe.get_doc("Payment Entry", data_import_doc)
	if data_import_doc:
		if data_import_doc.payment_type != "Receive" and data_import_doc.party_type != "Customer":
			frappe.throw(_("Payment Type must be Receive and Party Type must be Customer"))
		else: customer = data_import_doc.party

	import_log = []
	def log(**kwargs):
		import_log.append(kwargs)

	def as_link(doctype, name):
		return getlink(doctype, name)

	# publish realtime task update
	def publish_progress(achieved, reload=False):
		if data_import_doc:
			frappe.publish_realtime("payment_entry_progress", {"progress": str(int(100.0*achieved/total)),
				"data_import": data_import_doc.name, "reload": reload}, user=frappe.session.user)


	
	file_doc=frappe.get_doc("File",{"file_url":data_import_doc.attach_file, "attached_to_name": data_import_doc.name})

	if not file_doc:
		error_flag = True
		err_msg = err_msg + "File not found in the document attachment\n"

	fcontent = file_doc.get_content()
	filename, file_extension = file_doc.get_extension()

	if file_extension == '.xlsx' and from_data_import == 'No':
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(file_url=data_import_doc.attach_file)

	elif file_extension == '.xls':
		from frappe.utils.xlsxutils import read_xls_file_from_attached_file
		rows = read_xls_file_from_attached_file(fcontent)

	elif file_extension == '.csv':
		from frappe.utils.csvutils import read_csv_content
		rows = read_csv_content(fcontent, ignore_encoding_errors)
	else:
		error_flag = True
		err_msg = err_msg + "Unsupported File Format (only xlsx, xls and csv)" + "\n"

	data = rows or []
	total = len(data) or 1

	customer_doc = frappe.get_doc(data_import_doc.party_type, customer) or None

	if not customer_doc: 
		error_flag = True
		err_msg = err_msg + "Customer %s not found" % (customer) + "\n"

	data_import_doc.references = []
	data_import_doc.deductions = []
	data_import_doc.difference_amount = data_import_doc.unallocated_amount = 0

	#extract and map source data and populate outstanding invoices
	if not error_flag:
		for row_idx, row in enumerate(data, 1):
			#set max records to 300
			if row_idx > 300: break 

			val = ['',0,'',0] #order_id, amount, type:received;deduction, amount_col_idx
		
			for idx, d in enumerate(row,1):
				is_finish=0
				for mpm in customer_doc.marketplace_payment_mapper:
					if mpm.order_no_col_idx and mpm.order_no_col_idx == idx and not val[0] and d: #if order_no_col_idx is specified
						val[0] = cstr(d).split(".")[0]
						val[2] = mpm.type
						val[3] = mpm.amount_column_index

					s = '$'.join([cstr(d) for d in row if d]).split(mpm.keyword.strip()) if mpm.keyword else ""
					if len(s) > 1 and not val[0]: #keywords mapper matched
						try:
							if not val[0]:
								val[0] = s[1].split('$')[0].strip()
								val[2] = mpm.type
								val[3] = mpm.amount_column_index
								#err_msg = err_msg + "row %s. new match mpm %s. val: %s" % (cstr(row_idx),cstr(mpm.idx), cstr(val)) + "\n"
						except:
							error_flag = True
							err_msg = err_msg + 'Data Row %s. Could not get Order_ID for keyword "%s"' % (cstr(row_idx), cstr(s)) + "\n"

					'''
					if mpm.keyword.strip() in cstr(d): #get order_id
						try:
							val[0] = list(filter(None,cstr(d).split(mpm.keyword.strip())))[0].strip() or ""
							val[2] = cstr(mpm.type)
							#err_msg = err_msg + "row %s. getting order_id %s. type: %s" % (cstr(row_idx),cstr(val[0]), mpm.type)+ "\n"
						
						except:	
							error_flag = True
							err_msg = 'Data Row %s. Could not get Order ID "%s", please check data and mapper setting' % (cstr(row_idx), cstr(d))
					'''
					#if val[0] and val[3] == idx and not val[1]: #get payment amount
					if (val[0] and val[3] == idx) or (mpm.amount_column_index == idx and not val[1]): #if amount_column_idx comes before order_no_idx

						try:
							if (val[2] or mpm.type) == "Received": val[1] = flt(cstr(d)) or 0
							elif (val[2] or mpm.type) == "Deduction": val[1] = abs(flt(cstr(d))) * -1 or 0

							#err_msg = err_msg + "row %s. getting amount %s" % (cstr(row_idx),cstr(val)) + "\n"
							break
						except: 
							error_flag = True
							err_msg = err_msg + 'Data Row %s. Error getting amount value "%s", please check data and mapper setting' % (cstr(row_idx), cstr(d)) + "\n"
				#if val[0] and val[1]:
				#	frappe.throw("val[0] == " + cstr(val[0]) + ", val[1] == " + cstr(val[1]))
				#add payment entry invoices reference
				if not is_finish and val[0] and val[1] and frappe.db.exists("Sales Invoice",{"name":cstr(val[0]), "customer":customer or data_import_doc.party, "docstatus":1, "is_return":0, "outstanding_amount": (">", 0)}):	
					is_exists = 0
					inv = frappe.get_doc("Sales Invoice",{"name":val[0], "docstatus":1, "is_return": 0, "outstanding_amount": (">", 0)})
					received_amount = flt(val[1]) #inv.outstanding_amount if flt(val[1]) > inv.outstanding_amount else flt(val[1])

					if len(data_import_doc.references) > 0:
						for r in data_import_doc.references:
							if val[0] == r.reference_name:
								#err_msg = err_msg + "row %s. update existing %s. is_finish:%s" % (cstr(row_idx),cstr(val),cstr(is_finish)) + "\n"
								is_exists = 1
								r.ordered_amount = flt(r.ordered_amount) + received_amount
								total_allocated = r.allocated_amount + received_amount
								r.allocated_amount = inv.outstanding_amount #total_allocated if total_allocated <= inv.outstanding_amount else inv.outstanding_amount
								break

					if inv and not is_exists:	
						#err_msg = err_msg + "row %s. new row %s. is_finish:%s" % (cstr(row_idx),cstr(val), cstr(is_finish)) + "\n"				
						data_import_doc.append("references",
							{
								"reference_doctype": inv.doctype,
								"reference_name": inv.name,
								"due_date": inv.due_date,
								"total_amount": inv.grand_total,
								"outstanding_amount": inv.outstanding_amount,
								"ordered_amount": received_amount or 0,
								"allocated_amount": inv.outstanding_amount #received_amount if received_amount <= inv.outstanding_amount else inv.outstanding_amount
							})
					is_finish=1
					break


			publish_progress(row_idx)

	#calculate paid amount and deductions if over paid
	if data_import_doc.references:
		data_import_doc.difference_amount = 0
		data_import_doc.paid_amount = sum(d.ordered_amount for d in data_import_doc.references if d.ordered_amount)
		data_import_doc.received_amount = data_import_doc.paid_amount
		total_allocated = sum(d.allocated_amount for d in data_import_doc.references if d.allocated_amount)

		if flt(data_import_doc.paid_amount) != flt(total_allocated):
			marketplace_fee_account = frappe.get_value("Account",{"account_type":"Expense Account","disabled":0,"is_marketplace_fee_account":1},"name") or ""

			data_import_doc.deductions = []
			if marketplace_fee_account:
				data_import_doc.append("deductions",
					{
						"account": marketplace_fee_account,
						"cost_center": frappe.get_value("Company", data_import_doc.company, "cost_center") or "",
						"amount": flt(total_allocated) - flt(data_import_doc.paid_amount)
					})


	if len(data) < 1:
		error_flag = True
		err_msg = err_msg + "Attached file has no records" + "\n"


	#error_flag = True

	log_message = {"messages": data, "error": error_flag}

	if data_import_doc:
		#data_import_doc.log_details = json.dumps(log_message)
		data_import_doc.import_status = ""
		data_import_doc.error_message = ""
		#error_flag=True
		
		if error_flag:
			data_import_doc.import_status = "Failed"
			data_import_doc.error_message = err_msg or ""
		
		elif data_import_doc.references:
			data_import_doc.import_status = "Success"

		else: data_import_doc.import_status = "No records found"

		data_import_doc.save()
		if data_import_doc.import_status == "Success":
			publish_progress(100, True)
		else: publish_progress(0, True)

		frappe.db.commit()
		
	return log_message