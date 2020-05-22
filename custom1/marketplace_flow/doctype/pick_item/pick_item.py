# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time
from frappe.utils.dateutils import parse_date

class PickItem(Document):
	pass

	def onload(self):
		self.load_unpicked_items

	def get_conditions(self):
		conditions = []
	
		if self.store_name:
			conditions.append("si.customer=%(store_name)s")


		return "and {}".format(" and ".join(conditions)) if conditions else ""

	def load_unpicked_items(self):
		conditions = ""
		if self.store_name: 
			conditions += " and si.customer='{}'".format(self.store_name)

		items = frappe.db.sql("""Select si.name, si.awb_no, si.order_date, item.item_code,item.item_name, item.qty, item.picked_qty,item.is_picked
				from `tabSales Invoice` si join `tabSales Invoice Item` item on si.name=item.parent
				where item.qty > item.picked_qty and (ifnull(no_online_order,'') != '' or ifnull(awb_no,'') != '')
				and si.order_status in ('To Pick') and si.is_return=0 and si.docstatus=0 {conditions}
				order by si.creation asc limit 10""".format(conditions=conditions), as_dict=1)

		for row in items:
			if row:
				self.append("items",{
						"order_no": row.name,
						"awb_no": row.awb_no,	
						"order_date": row.order_date,
						"item_code": row.item_code,
						"item_name": row.item_name,
						"order_qty": row.qty,
						"picked_qty": row.picked_qty,
						"is_picked": row.is_picked
					})
		

@frappe.whitelist()
def update_picked_item(awb_order_no, serial_batch_no, item_code):
	message=[0,0,0,"","",""] #order_qty, picked_qty, is_picked, error_msg, item_code, item_image_url
	is_item_empty=True

	image_url=None

	si = frappe.db.sql('''select name from `tabSales Invoice` where docstatus=0 and is_return=0 and (no_online_order=%s or awb_no=%s) limit 1''', (awb_order_no,awb_order_no),as_dict=0) or ""

	''' get si item '''
	if si:
		doc = frappe.get_doc("Sales Invoice",cstr(si[0][0]))

		''' get item_code if user scan item barcode '''
		sku = frappe.db.sql('''select it.name from `tabItem` it join `tabItem Barcode` bar on it.name=bar.parent
			where it.disabled=0 and it.is_stock_item=1 and bar.barcode=%s limit 1''', (item_code), as_dict=0)
		if sku:
			item_code =  cstr(sku[0][0]) or item_code or ""

		if item_code:
			image_url = frappe.db.get_value("File",{"attached_to_name": item_code},"thumbnail_url") or ""
			if image_url: message[5] = image_url

		for d in doc.items:
			if d.item_code == item_code:
				is_item_empty = False
				is_counted = True
				message[4] = d.item_code

				if not d.warehouse:
					d.warehouse = frappe.db.get_value("User Permission", {"user":frappe.session.user, "allow":"Warehouse"}, "for_value") or \
						frappe.db.get_single_value('Stock Settings', 'default_warehouse') or ""

				if serial_batch_no:
					if frappe.db.get_value("Item", item_code, "has_serial_no"):
						serial_list=[]
						if d.serial_no:
							serial_list = d.serial_no.strip().split("\n")

						serial_nos = frappe.get_list("Serial No", fields="name", filters = [["name","=",serial_batch_no.strip()],["delivery_document_no","=",""], ["status", "not in", ["Expired","Delivered"]]])

						if (len(serial_list) < 1 or serial_batch_no.strip() not in serial_list) and serial_nos:
							d.serial_no = cstr(d.serial_no) + serial_nos[0].name + "\n"
						elif item_code != serial_batch_no: 
							message[3] = 'Failed: Serial "%s" is not valid (Delivered / Not Active / Not Exists)' % (serial_batch_no) 
							return message

					if frappe.db.get_value("Item", item_code, "has_batch_no"):
						from erpnext.stock.doctype.batch.batch import get_batch_qty
						batch_qty = get_batch_qty(serial_batch_no.strip(), d.warehouse, d.item_code) or 0.0
						batch_id = frappe.db.get_value("Batch", {"name":serial_batch_no.strip(), "disabled":0}, "batch_id") or ""
						if batch_qty >= d.qty and batch_id:
							d.batch_no = batch_id
						elif batch_id and item_code != serial_batch_no:
							message[3] = 'Failed: Batch "%s" has %s < %s in %s' % (serial_batch_no.strip(), cstr(batch_qty), cstr(d.qty), d.warehouse)
							return message

				if d.qty > d.picked_qty:
					message[0]=d.qty

					d.picked_qty += 1

					message[1] = d.picked_qty
	
					if d.picked_qty == d.qty:
						d.is_picked = 1
						message[2] = d.is_picked
						message[3] = "Completed"
						d.picked_time = now_datetime()
						doc.save()

						#check whether all items are packed then change status
						if not frappe.db.get_values("Sales Invoice Item", {"parent":doc.name,"is_picked":"0"},"item_code"):
							doc.order_status = "To Pack"
							doc.save()

					frappe.db.commit()

					return message
					
				else:
					message[3] = "Error: Over Picked Qty"
					return message

		if is_item_empty:
			message[3] = "Error: Item Code / SKU not found in this order"
			return message
	else:
		message[3] = "Error: Order No / AWB Not Found"
		return message
	