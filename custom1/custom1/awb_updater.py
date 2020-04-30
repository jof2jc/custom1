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
from frappe.core.doctype.data_import.importer import upload
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
def update_awb(data_import):
	frappe.db.set_value("Data Import", data_import, "import_status", "In Progress", update_modified=False)
	frappe.publish_realtime("data_import_progress", {"progress": "0",
		"data_import": data_import, "reload": True}, user=frappe.session.user)

	from frappe.core.page.background_jobs.background_jobs import get_info
	enqueued_jobs = [d.get("job_name") for d in get_info()]

	if data_import not in enqueued_jobs:
		#enqueue(execute_update_awb(data_import), queue='default', timeout=1000, job_name=data_import,
		#	data_import_doc=data_import, user=frappe.session.user)
		enqueue(execute_update_awb, queue='default', timeout=1000, event='data_import', job_name=data_import,
			data_import_doc=data_import, from_data_import="Yes", user=frappe.session.user)


def execute_update_awb(rows = None, submit_after_import=None, ignore_encoding_errors=False, no_email=True, overwrite=None,
	update_only = None, ignore_links=False, pre_process=None, via_console=False, from_data_import="No",
	skip_errors = True, data_import_doc=None, validate_template=False, user=None):

	error_flag = rollback_flag = False
	data = data_with_error = []
	import_Status = ""
	total=0

	data_import_doc = frappe.get_doc("Data Import", data_import_doc)

	import_log = []
	def log(**kwargs):
		import_log.append(kwargs)

	def as_link(doctype, name):
		return getlink(doctype, name)

	# publish realtime task update
	def publish_progress(achieved, reload=False):
		if data_import_doc:
			frappe.publish_realtime("data_import_progress", {"progress": str(int(100.0*achieved/total)),
				"data_import": data_import_doc.name, "reload": reload}, user=frappe.session.user)


	def update_awb_dict(mydict, skip_errors=0, idx=1, rollback_flag=False):
		try: 
			doc = frappe._dict()
			if frappe.db.get_value(data_import_doc.reference_doctype, {"name":mydict.order_no,"is_return":0},"name"):
				doc = frappe.get_doc(data_import_doc.reference_doctype, {"name":mydict.order_no,"is_return":0})
			if doc:
				if mydict.awb_no[-8:].isdigit() or "TJNE-" in mydict.awb_no: #check awb format is correct, last 8 digits must be number
					if not doc.awb_no and mydict.awb_no and doc.docstatus == 0:
						doc.awb_no = mydict.awb_no

						log(**{"row": idx, "title": 'Updated AWB "%s" for "%s"' % (mydict.awb_no, as_link(doc.doctype, doc.name)),
							"link": "", "message": 'Document successfully updated', "indicator": "green"
						})
						doc.save()

					elif doc.awb_no and doc.awb_no != mydict.awb_no and doc.docstatus == 0:
						log(**{"row": idx, "title": 'Updated AWB "%s" for "%s"' % (mydict.awb_no, as_link(doc.doctype, doc.name)),
							"link": "", "message": 'Different AWB "%s" found. Document successfully updated' % (doc.awb_no), "indicator": "blue"
						})
						doc.awb_no = mydict.awb_no
						doc.save()

					elif doc.awb_no and doc.docstatus == 0:
						log(**{"row": idx, "title": 'AWB "%s" was updated for "%s"' % (mydict.awb_no, as_link(doc.doctype, doc.name)),
							"link": "", "message": 'Ignored', "indicator": "orange"
						})
					elif doc.docstatus == 1:
						log(**{"row": idx, "title": 'Order "%s" is delivered' % (mydict.order_no),
							"link": "", "message": 'AWB "%s" not updated. Ignored' % (mydict.awb_no), "indicator": "orange"
						})
					elif doc.docstatus == 2:
						log(**{"row": idx, "title": 'Order "%s" is cancelled' % (mydict.order_no),
							"link": "", "message": 'AWB "%s" not updated. Ignored' % (mydict.awb_no), "indicator": "orange"
						})
				else:
					log(**{"row": idx, "title": 'Wrong AWB Format "%s"' % (mydict.awb_no),
							"link": "", "message": 'Order "%s"' % (mydict.order_no), "indicator": "orange"
						})

			elif not mydict.awb_no:
				log(**{"row": idx, "title": 'AWB not found in the Print Slip',
					"link": "", "message": 'Order "%s". Please check Print-Slip.pdf' % (mydict.order_no), "indicator": "orange"
				})
			else:
				log(**{"row": idx, "title": 'Order "%s" not found' % (mydict.order_no),
					"link": "", "message": 'AWB "%s" not updated. Skipped' % (mydict.awb_no), "indicator": "orange"
				})

			data.append(mydict)

		except Exception as e:
			error_flag = True
			err_msg = error_link = ""

			# build error message
			if frappe.local.message_log:
				err_msg = "\n".join(['<p class="border-bottom small">{}</p>'.format(json.loads(msg).get('message')) for msg in frappe.local.message_log])
			else:
				err_msg = '<p class="border-bottom small">{}</p>'.format(cstr(e))

			error_trace = frappe.get_traceback()
			if error_trace:
				error_log_doc = frappe.log_error(error_trace)
				error_link = ""
			else:
				error_link = None

			log(**{
				"row": idx,
				"title": 'Error for AWB "%s" for Order "%s"' % (mydict.awb_no, mydict.order_no),
				"message": err_msg,
				"indicator": "red",
				"link":error_link
			})

			if skip_errors:
				data_with_error.append(mydict)
			else:
				rollback_flag = True

		if rollback_flag:
			frappe.db.rollback()
		else:
			frappe.db.commit()



	
	file_doc=frappe.get_doc("File",{"file_url":data_import_doc.import_file, "attached_to_name": data_import_doc.name})
	if not file_doc:
		frappe.throw("Please attach the file first")

	''' Tokopedia and BUkalapak '''
	if ".htm" in cstr(data_import_doc.import_file):
		from bs4 import BeautifulSoup

		f = open(file_doc.get_full_path())

		soup = BeautifulSoup(f, "html.parser")

		if "TOKOPEDIA" in cstr(data_import_doc.import_file).upper():				
			table = soup.findAll('table',{'class':'meta'})
			total = len(table)
			data_import_doc.total_rows = total

			for i, line in enumerate(table):
				mydict=frappe._dict()
				idx=i+1

				#l = len(line.findAll('dd'))
				for td in line.findAll('td'):
					a = td.text.replace(" ","").replace("\n\n","").replace("\n","").strip()
				
					if len(mydict)==0 and "order_no" not in mydict and a:
						mydict["order_no"]=a
					elif len(mydict)==1 and "courier" not in mydict and a:
						mydict["courier"]=a
					elif len(mydict)==2 and "berat" not in mydict and a:
						mydict["berat"]=a
					elif len(mydict)==3 and "ongkir" not in mydict and a:
						mydict["ongkir"]=a	
					elif len(mydict)==4 and "awb_no" not in mydict and a:
						awb_no = cstr(td.text.split()[0])
						if (awb_no): mydict["awb_no"]=awb_no.strip()

						if len(mydict) == 5:
							update_awb_dict(mydict, data_import_doc.skip_errors, len(data)+1)
				publish_progress(i+1)
		
		elif "BUKALAPAK" in cstr(data_import_doc.import_file).upper():
				
			table = soup.findAll('div',{'class':'transaction-slip'})
			total = len(table)
			data_import_doc.total_rows = total

			for i, line in enumerate(table):
				mydict=frappe._dict()
				idx=i+1
	
				for div in line.findAll('div',{'class':'row section-logistic-booking'}): #kode-booking AWB
					awb_no = str(div.text.split()[2])
					if awb_no and len(mydict)==0 and "awb_no" not in mydict:
						mydict["awb_no"] = awb_no.strip()

					n=0
					
					for dd in line.findAll('dd',{'class':'text bukalapak-transaction-slip-buyer--name'}):
						a = dd.text.strip()

						if len(mydict)==1 and "ongkir" not in mydict and a:
							mydict["ongkir"]=a
						elif len(mydict)==2 and "order_no" not in mydict and a and n==3:
							mydict["order_no"]=a
						elif len(mydict)==3 and "courier" not in mydict and a and n==4:
							mydict["courier"]=a
						elif len(mydict)==4 and "berat" not in mydict and a and n==5:
							mydict["berat"]=a

							if len(mydict) == 5:
								update_awb_dict(mydict, data_import_doc.skip_errors, len(data)+1)
						n += 1

				publish_progress(i+1)
		f.close()

	elif ".pdf" in cstr(data_import_doc.import_file): #SHopee
		f = open(file_doc.get_full_path(), 'rb')
		rsrcmgr = PDFResourceManager()
		laparams = LAParams()
		device = PDFPageAggregator(rsrcmgr, laparams=laparams)
		interpreter = PDFPageInterpreter(rsrcmgr, device)
		pages = PDFPage.get_pages(f)

		parser = PDFParser(f)
		document = PDFDocument(parser)

		total = resolve1(document.catalog['Pages'])['Count']
		data_import_doc.total_rows = total

		for p, page in enumerate(pages):

			mydict=frappe._dict()

			interpreter.process_page(page)
			layout = device.get_result()
			
			for i, lobj in enumerate(layout):
				#l = [0,3,5,8]

				if isinstance(lobj, LTTextBox):
					x, y, text = lobj.bbox[0], lobj.bbox[3], lobj.get_text()

					''' JNE REG, JNE TRUCK, SiCepat '''
					if len(mydict)==0 and "awb_no" not in mydict and text:
						if '535.76' in cstr(y) or '532.76' in cstr(y) or '535.01' in cstr(y):
							mydict["awb_no"]=text.strip()
					elif len(mydict)==1 and "order_no" not in mydict and text:
						if '465.75' in cstr(y): #JNE REG
							mydict["order_no"]=text.strip()
						elif '514.47' in cstr(y): #JTR
							order_no = text.split(':')[1].strip()
							mydict["order_no"] = order_no.split("\n")[0]
						elif '520.01' in cstr(y): #siCepat
							order_no = text.split(':')[1].strip()
							mydict["order_no"] = order_no.split("\n")[0]

						if len(mydict) == 2: 
							update_awb_dict(mydict, data_import_doc.skip_errors, len(data)+1)
							mydict=frappe._dict()

			publish_progress(i+1)

		f.close()

	else:
		error_flag = True
		data_import_doc.skip_errors = 0
		import_log=[]
		log(**{
			"row": "1",
			"title": "Error file type or name",
			"message": "Please check file type is pdf or html, also file_name must includes marketplace name like Tokopedia, Shopee, Bukalapak etc",
			"indicator": "red",
			"link":""
		})


	log_message = {"messages": import_log, "error": error_flag}

	if data_import_doc:
		data_import_doc.log_details = json.dumps(log_message)

		import_status = None
		if error_flag and data_import_doc.skip_errors and len(data) != len(data_with_error):
			import_status = "Partially Successful"
		elif error_flag:
			import_status = "Failed"
		elif not error_flag:
			import_status = "Successful"

		data_import_doc.import_status = import_status
		data_import_doc.save()
		if data_import_doc.import_status in ["Successful", "Partially Successful"]:
			data_import_doc.submit()
			publish_progress(100, True)
			frappe.db.commit()
		else:
			publish_progress(0, True)
		
	else:
		return log_message