# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time, get_site_name


class MarketplaceOutbondReceipt(Document):
	pass

	def get_last_pickup_session(self, courier=""):
		if not self.customer:
			frappe.throw("Please select Customer / Store first!")
		elif not courier:
			frappe.throw("Please select Courier table!")

		last_session = frappe.db.sql('''select parent.pickup_session from `tabMarketplace Outbond Receipt` parent join `tabMarketplace Courier Reference` child
			on parent.name=child.parent where parent.docstatus=1 and parent.name != %s and parent.customer=%s and parent.date=%s and child.marketplace_courier=%s order by parent.creation desc limit 1''', (self.name, self.customer, self.date, courier), as_dict=0)

		if last_session:
			return last_session[0][0]
		else: return "0"

	def validate(self):
		if not self.label_list:
			frappe.throw(_("Label List cannot be empty"))
		elif not self.courier_references:
			frappe.throw(_("Please specify courier table"))

		self.title = ""
		for d in self.courier_references:
			if not self.title:
				self.title = d.marketplace_courier
			else: self.title = self.title + "-" + d.marketplace_courier
		

	def before_submit(self):
		if self.label_list:
			awb_list = self.label_list.strip().split("\n")
			self.label_list = "" #empty label list and rebuild

			idx=0
			for d in awb_list:
				if d and frappe.db.exists("Sales Invoice",{"awb_no" or "name":d.strip(), "docstatus":1, "order_status":"Completed"}):
					doc = frappe.get_doc("Sales Invoice", {"awb_no" or "name":d.strip(), "docstatus":1, "order_status":"Completed"})
					doc.db_set("order_status","Delivered")
					doc.db_set("delivery_date",now_datetime())

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
				if d and frappe.db.exists("Sales Invoice",{"awb_no":d, "docstatus":1, "order_status":"Delivered"}):
					doc = frappe.get_doc("Sales Invoice", {"awb_no":d, "docstatus":1, "order_status":"Delivered"})
					doc.db_set("order_status","Completed")
					doc.db_set("delivery_date","")

					frappe.db.commit()