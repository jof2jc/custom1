from __future__ import unicode_literals
import frappe
from frappe import _

import json
from frappe.utils import flt, cstr, nowdate, nowtime

def set_return_details(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	print company
	#frappe.throw(_("Company is {0}").format(company))

	if company != "IMPERIAL MEGA PRIMA":
		return
	if self.doctype not in ("Stock Entry", "Sales Invoice", "Purchase Invoice"):
		return

	for d in self.items:
		serial_nos = cstr(d.serial_no).strip().replace(',', '\n').split('\n')
		print serial_nos
		if not serial_nos:
			return

		for imei in serial_nos:
			serial_doc = frappe.get_doc("Serial No", imei)

			print self.doctype
			print imei 

			if self.doctype == "Stock Entry":
				if (self.return_from_customer and self.purpose == "Material Receipt"):
					serial_doc.return_from_customer = self.return_from_customer
				elif (self.ship_to_service_supplier and self.purpose == "Material Transfer"):
					serial_doc.ship_to_service_supplier = self.ship_to_service_supplier
			else:
				serial_doc.ship_to_service_supplier = ""
				serial_doc.return_from_customer = ""

			serial_doc.save()