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
				and si.is_return=0 and si.docstatus=0 {conditions}
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
	message=[0,0,0,""]

	si = frappe.db.sql('''select name from `tabSales Invoice` where docstatus=0 and is_return=0 and (name=%s or awb_no=%s) limit 1''', (awb_order_no,awb_order_no),as_dict=0) or ""

	''' get si item '''
	if si:
		doc = frappe.get_doc("Sales Invoice",cstr(si[0][0]))

		for d in doc.items:
			if d.item_code == item_code:
				if serial_batch_no:
					if frappe.db.get_value("Item", item_code, "has_serial_no"):
						d.serial_no = cstr(d.serial_no) + serial_batch_no + "\n"
					elif frappe.db.get_value("Item", item_code, "has_batch_no"):
						d.batch_no = serial_batch_no

				if d.qty > d.picked_qty:
					message[0]=d.qty

					d.picked_qty += 1

					message[1] = d.picked_qty
			
					if d.picked_qty == d.qty:
						d.is_picked = 1
						message[2] = d.is_picked

					#doc.save()
					#frappe.db.commit()
					
					if d.picked_qty == d.qty:
						message[3] = "Completed"

					return message
					
				else:
					message[3] = "Error: Over Picked Qty"
					return message

	else:
		message[3] = "Error: Order / AWB Not Found"
		return message
	