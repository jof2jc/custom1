# -*- coding: utf-8 -*-
# Copyright (c) 2018, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate
from frappe.model.naming import make_autoname
from frappe.model.document import Document

class OnlineShippingLog(Document):
	pass

	def before_insert(self):
		if not self.awb_no:
			frappe.throw(_("AWB No is required"))
		else:
			if frappe.db.get_value("Online Shipping Log", {"name":self.awb_no.strip()}, "name"):
				frappe.throw(_("Same AWB No exists : {0}").format(self.awb_no))

		invoice = frappe.db.get_value("Sales Invoice", {"awb_no":self.awb_no, "docstatus":"1"}, ["name","shipping_fee"])

		#frappe.throw(_("Invoice : {0}").format(cstr(invoice[1])))
		if invoice:
			self.shipping_fee = cstr(invoice[1]) or "0"
			self.invoice_no = invoice[0] or ""
		else:
			frappe.msgprint(_("Invoice / Order No not found")) 

	def validate(self):
		self.before_insert()

	def on_submit(self): 
		if self.invoice_no:
			si = frappe.get_doc("Sales Invoice",self.invoice_no)

			if si and self.actual_shipping_fee:
				si.actual_shipping_fee = self.actual_shipping_fee
				if not si.awb_no:
					si.awb_no = self.awb_no
				si.save()

