# -*- coding: utf-8 -*-
# Copyright (c) 2018, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate
from frappe.model.naming import make_autoname
from frappe.model.document import Document
from frappe.utils.data import format_datetime
from re import sub
from decimal import Decimal

class OnlineShippingLog(Document):
	pass

	def autoname(self):
		courier = ""

		if self.courier:
			courier = "-"+self.courier

		if self.awb_no:
			self.name = self.awb_no + courier + " on "+ format_datetime(self.creation)
		else:
			self.name = "Log on "+ format_datetime(self.creation)

	def before_insert(self):
		if not self.awb_no:
			frappe.throw(_("AWB No is required"))
				
		'''
		else:
			if frappe.db.get_value("Online Shipping Log", {"name":self.awb_no.strip()}, "name"):
				frappe.throw(_("Same AWB No exists : {0}").format(self.awb_no))
		'''

		invoice = ""
		invoice = frappe.db.get_value("Sales Invoice", {"awb_no":self.awb_no, "docstatus":"1", "is_return":"0"}, ["name","shipping_fee","awb_no","actual_shipping_fee"]) or \
			frappe.db.get_value("Sales Invoice", {"no_online_order":self.invoice_no, "docstatus":"1", "is_return":"0"}, ["name","shipping_fee","awb_no","actual_shipping_fee"])

		if self.awb_no and not invoice:
			#actual_shipping_fee = frappe.db.sql('''select actual_shipping_fee from `tabOnline Shipping Log` where awb_no=%s and ifnull(actual_shipping_fee,0) > 0 limit 1''', (self.awb_no), as_dict=0)

			#if actual_shipping_fee:
			#	frappe.throw(_("AWB: {0} with actual shipping fee: {1} exists. No update required").format(self.awb_no, cstr(actual_shipping_fee[0][0])))
			if not self.actual_shipping_fee:
				frappe.throw(_("Actual shipping fee is required if Order ID not found : {0}. Please upload AWB/Resi from marketplace first").format(self.awb_no))
			elif not self.courier:
				frappe.throw(_("Courier name is required"))

		elif invoice:
			#if invoice[3]:
			#	frappe.throw(_("Actual shipping fee: {0} is found for AWB: {1} and Order: {2}. No update required").format(cstr(invoice[3]), self.awb_no, cstr(invoice[0])))
				
			self.shipping_fee = cstr(invoice[1]) or "0"
			self.invoice_no = invoice[0] or ""
			'''
			if cstr(invoice[2]) and cstr(invoice[2]) == self.awb_no.strip():
				if not self.actual_shipping_fee:
					frappe.throw(_("Order: {0} found. Actual shipping fee is required").format(cstr(invoice[0])))
				elif not self.actual_weight:
					frappe.throw(_("Order: {0} found. Actual weight is required").format(cstr(invoice[0])))
					#frappe.throw(_("AWB: {0} was linked with Order: {1}").format(self.awb_no, cstr(invoice[0])))
			'''

		if not self.bill_date:
			self.bill_date = nowdate()
		self.latest = 2

		actual_shipping_fee = cstr(Decimal(sub(r'[^\d.]', '', cstr(self.actual_shipping_fee or "0"))))
		actual_insurance_fee = cstr(Decimal(sub(r'[^\d.]', '', cstr(self.actual_insurance_fee or "0"))))
		actual_weight = self.actual_weight

		self.actual_shipping_fee = cstr(actual_shipping_fee).replace(".","")
		self.actual_insurance_fee = cstr(actual_insurance_fee).replace(".","")
		self.actual_weight = flt(actual_weight)
		

	#def validate(self):
	#	self.before_insert()

	def on_submit(self): 
		latest_awb = frappe.db.sql('''select name from `tabOnline Shipping Log` where awb_no=%s and docstatus=1 and latest=1 limit 1''', (self.awb_no), as_dict=0)
		if latest_awb:
			before_doc = frappe.get_doc("Online Shipping Log",cstr(latest_awb[0][0]))
			before_doc.latest = 0
			before_doc.save()	#update before_doc

		self.latest = 1  #set current_doc as latest
		self.save()

		invoice_no = frappe.db.get_value("Sales Invoice", {"awb_no":self.awb_no, "docstatus":"1", "is_return":"0"}, "name") or \
			frappe.db.get_value("Sales Invoice", {"no_online_order":self.invoice_no, "docstatus":"1", "is_return":"0"}, "name")

		if invoice_no:			
			si = frappe.get_doc("Sales Invoice",frappe.db.get_value("Sales Invoice", {"no_online_order":cstr(invoice_no), "docstatus":"1", "is_return":"0"}, "name"))

			if si and self.awb_no:
				si.actual_shipping_fee = self.actual_shipping_fee if self.actual_shipping_fee else 0.0
				si.actual_insurance_fee = self.actual_insurance_fee if self.actual_insurance_fee else 0.0
				si.awb_no = self.awb_no

				#if si.awb_no != self.awb_no or si.actual_shipping_fee != self.actual_shipping_fee or si.actual_insurance_fee !=self.actual_insurance_fee:
				si.save()

