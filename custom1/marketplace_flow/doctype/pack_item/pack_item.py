# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time, time_diff_in_hours
from frappe.utils.dateutils import parse_date
import json
from custom1.marketplace_flow.marketplace_flow import validate_mandatory

class PackItem(Document):
	pass

	def get_conditions(self):
		conditions = []
	
		if self.store_name:
			conditions.append("si.customer=%(store_name)s")


		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def load_item_details(self):
		scan_data=""
		if self.type == "Scan Start" and self.scan_start:
			scan_data = self.scan_start.strip()
		elif self.type == "Scan End" and self.scan_end: 
			scan_data = self.scan_end.strip()

		if not scan_data: return
		
		item_log = []
		def log(**kwargs):
			item_log.append(kwargs)

		doc=None
		invoice = frappe.db.sql('''select name from `tabSales Invoice` where is_return=0 and (no_online_order=%s or awb_no=%s) order by creation desc limit 1''', (scan_data,scan_data),as_dict=0) or ""

		if invoice:
			doc = frappe.get_doc("Sales Invoice",cstr(invoice[0][0]))


		if self.send_to_qc and doc:
			if doc.docstatus == 0 and doc.order_status in ("To Pack"):
				doc.order_status = "Send to QC"
				doc.save()
				frappe.db.commit()
				self.status = 'Success updated status "Send to QC" for "%s"' % (scan_data)
			else:
				self.status = "Not found or already packed"
			return

		if doc:
			if doc.order_status not in ("To Pack") and doc.docstatus == 0:
				self.status = 'Status "%s" is invalid: %s' % (doc.name, doc.order_status)
				return
			elif doc.docstatus == 1 :
				self.status = '"%s" is submitted. Status: %s' % (scan_data, doc.order_status)
				return
			elif doc.docstatus == 2 :
				self.status = '"%s" is cancelled. Status: %s' % (scan_data, doc.order_status)
				return

		elif not doc:
			self.status = '"%s" not found' % (scan_data)
			return log_message


		conditions = ""
		#if self.store_name: 
		#	conditions += " and si.customer='{}'".format(self.store_name)

		items = frappe.db.sql("""Select si.name, si.awb_no, si.order_date, si.order_status, si.package_weight, 
			si_item.item_code,si_item.item_name, si_item.qty, si_item.is_picked, ifnull(f.thumbnail_url,'') as image
			from `tabSales Invoice` si join `tabSales Invoice Item` si_item on si.name=si_item.parent
			join `tabItem` it on it.item_code=si_item.item_code left join `tabFile` f on f.attached_to_name=it.item_code
			where si.order_status in ('To Pack') and (ifnull(no_online_order,'') != '' or ifnull(awb_no,'') != '') and si.is_return=0 and si.docstatus=0 and 
			(si.no_online_order=%s or si.awb_no=%s) {conditions}""".format(conditions=conditions), (scan_data, scan_data), as_dict=1)


		for idx,row in enumerate(items):
			if row:
				#if not doc: 
				#	doc = frappe.get_doc("Sales Invoice",row.name)

				log(**{
					"row": idx + 1,
					"order_no":row.name,
					"awb_no":row.awb_no,
					"order_date":cstr(formatdate(row.order_date)),
					"order_status": row.order_status,
					"package_weight":row.package_weight,
					"is_picked":row.is_picked,
					"item_code":row.item_code,
					"item_name": row.item_name,
					"image":row.image,
					"qty":row.qty
				})

		#update paking_start _time
		if doc and self.type == "Scan Start":
			msg = validate_mandatory(doc)
			if msg:
				self.status = msg
				return

			if not doc.packing_start and doc.order_status in ("To Pack") and doc.docstatus == 0: 
				doc.packing_start = now_datetime()
				doc.save()

				''' insert marketplace scorecard '''
				if not frappe.db.exists("Marketplace Fulfillment Score Card",{"transaction_ref_no":doc.name, "type":"Packer"}) and \
					frappe.get_list("Score Card Template",fields=["name"],filters=[["score_type","=","Packer"]]):
					scorecard = frappe.new_doc("Marketplace Fulfillment Score Card")
					scorecard.type = "Packer"
					scorecard.transaction_ref_no = doc.name
					scorecard.time_start = doc.packing_start
					scorecard.insert()
				
				frappe.db.commit()
			else:
				self.status = '"%s" is already scanned start' % (doc.name)
				
			self.packing_start_time = doc.packing_start
			self.packing_end_time = doc.packing_end

		elif doc and self.type == "Scan End":
			validate_mandatory(doc)
			if doc.order_status in ("To Pack") and doc.docstatus == 0: 
				if not doc.packing_end or doc.amended_from:	
					doc.packing_end = now_datetime()

					#submit invoice
					doc.flags.ignore_permissions = True
					doc.posting_date = nowdate()
					doc.posting_time = nowtime()

					doc.delivery_date = nowdate()
					doc.picked_and_packed = 1
					doc.order_status = "Completed"

					doc.save()
					doc.submit()

					#update score_card time_end
					if frappe.db.exists("Marketplace Fulfillment Score Card",{"transaction_ref_no":doc.name, "type":"Packer"}):
						scorecard = frappe.get_doc("Marketplace Fulfillment Score Card",{"transaction_ref_no":doc.name, "type":"Packer"}) 
						scorecard.time_end = doc.packing_end
						hour_diff = time_diff_in_hours(scorecard.time_end, scorecard.time_start)

						score_list = frappe.get_list("Score Card Template",fields=["name"],filters=[["time_factor",">=",hour_diff],["score_type","=","Packer"]],order_by="time_factor")
						if score_list:
							scorecard.score = score_list[0].name
						scorecard.save()

					frappe.db.commit()
			
					self.status = '"%s" is submitted successfully' % (doc.name)
				else:
					self.status = '"%s" is already scanned end' % (doc.name)

			self.packing_start_time = doc.packing_start	
			self.packing_end_time = doc.packing_end

		log_message = {"messages": item_log, "error_flag": "0"}
		self.items_log = json.dumps(log_message)
		self.total_rows = len(items) or "0"
		return log_message

