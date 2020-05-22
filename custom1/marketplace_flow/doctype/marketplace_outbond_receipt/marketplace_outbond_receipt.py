# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class MarketplaceOutbondReceipt(Document):
	pass

	def validate(self):
		if not self.label_list:
			frappe.throw(_("Label List cannot be empty"))

	def before_submit(self):
		if self.label_list:
			awb_list = self.label_list.strip().split("\n")
			self.label_list = "" #empty label list and rebuild

			idx=0
			for d in awb_list:
				if d and frappe.db.exists("Sales Invoice",{"no_online_order":d, "docstatus":1, "order_status":"Completed"}):
					doc = frappe.get_doc("Sales Invoice", {"no_online_order":d, "docstatus":1, "order_status":"Completed"})
					doc.db_set("order_status","Delivered")

					self.label_list = self.label_list + d + "\n"
					idx += 1
				elif d:
					frappe.msgprint("Removed {0}. Status is not valid".format(d))

			self.total_package = idx
			if idx > 0:		
				frappe.db.commit()
			else:
				frappe.throw(_("Not valid. All labels are already delivered"))

	def on_cancel(self):
		if self.label_list:
			awb_list = self.label_list.strip().split("\n")
	
			for d in awb_list:
				if d and frappe.db.exists("Sales Invoice",{"no_online_order":d, "docstatus":1, "order_status":"Delivered"}):
					doc = frappe.get_doc("Sales Invoice", {"no_online_order":d, "docstatus":1, "order_status":"Delivered"})
					doc.db_set("order_status","Completed")
					frappe.db.commit()