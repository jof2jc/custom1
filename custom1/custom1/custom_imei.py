from __future__ import unicode_literals
import frappe
from frappe import _

import json
from frappe.utils import flt, cstr, nowdate, nowtime

@frappe.whitelist()
def imp_get_unpaid_installment_invoice(invoice_no):
	return frappe.db.sql('''select si.name, it.installment_no, it.amount from `tabSales Invoice` si, `tabSales Invoice Installment` it 
		where si.name=it.parent and si.name=%s and si.docstatus=1 and it.status="Unpaid"  
		and it.amount > 0 Order By it.installment_no ASC limit 1''', invoice_no, as_dict=0)

@frappe.whitelist()
def populate_item_details(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	print company
	#frappe.throw(_("Company is {0}").format(company))

	if company != "IMPERIAL MEGA PRIMA":
		return

	#self.set('items', {}) #clear item
	self.items = {}
	row = {}

	serial_nos = cstr(self.serial_nos).strip().replace(',', '\n').split('\n') if self.serial_nos else []

	#remove dupicates
	valid_serial_nos = []
	for val in serial_nos:
		if val:
			val = val.strip()
			if val not in valid_serial_nos:
				valid_serial_nos.append(val)

	for imei in valid_serial_nos:
		from erpnext.stock.get_item_details import get_item_details, get_item_code
		#from erpnext.stock.doctype.serial_no.serial_no import get_item_details import get_item_details
		item_code = get_item_code(None, imei)

		args = {
				"company": company,
				"currency": self.currency,
				"customer": self.customer,
				"price_list": self.selling_price_list,
				"price_list_currency": self.price_list_currency,	
				"conversion_rate": self.conversion_rate,
				"plc_conversion_rate": self.plc_conversion_rate,
				"is_pos": self.is_pos,
				"item_code": item_code,
				"update_stock": self.update_stock,
				"transaction_date": self.posting_date,
				"ignore_pricing_rule": self.ignore_pricing_rule,
				"doctype": self.doctype
			}

		items_dict = get_item_details(args)

		#check if imei exists in items
		is_exists = 0
		for item in self.items:
			#item.serial_no = ""
			#item_serial = cstr(item.serial_no).strip().replace(',', '\n').split('\n')

			if item.item_code == item_code: #item is found, append imei
				is_exists = 1
				item.serial_no = item.serial_no + imei + "\n"	
				item.qty += 1
				
		if is_exists == 0:
			row = self.append("items", {})
			row.serial_no = ""

			for f in items_dict:
				if not row.get(f):
					row.set(f, items_dict.get(f))
					if f == "rate":
						row.set(f, items_dict.get("price_list_rate"))

			row.serial_no = imei + "\n"
	self.save()



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
		
		has_serial_no = frappe.db.get_value("Item", d.item_code, "has_serial_no")

		if has_serial_no and serial_nos:

			for imei in serial_nos:
				serial_doc = frappe.get_doc("Serial No", imei)

				print self.doctype
				#print self.ship_to_service_supplier 
	
				if self.doctype == "Stock Entry":
					if (self.return_from_customer and self.purpose in ("Material Receipt", "Material Issue")):
						serial_doc.return_from_customer = self.return_from_customer

						if self.purpose == "Material Issue":
							serial_doc.qty = 0

					elif (self.ship_to_service_supplier and self.purpose == "Material Transfer"):
						serial_doc.ship_to_service_supplier = self.ship_to_service_supplier
						serial_doc.qty = 1

					elif self.purpose == "Material Issue":
						serial_doc.ship_to_service_supplier = ""
						serial_doc.return_from_customer = ""
						serial_doc.qty = 0
						if self.docstatus == 2:
							serial_doc.qty = 1
				else:
					serial_doc.ship_to_service_supplier = ""
					serial_doc.return_from_customer = ""
	
					if self.doctype == "Sales Invoice":
						if self.is_return or self.docstatus == 2:
							serial_doc.qty = 1
						else:
							serial_doc.qty = 0
					elif self.doctype == "Purchase Invoice":
						if self.is_return or self.docstatus == 2:
							serial_doc.qty = 0
						else:
							serial_doc.qty = 1

				serial_doc.save()

def imp_update_installment_payment_details(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	print company
	#frappe.throw(_("Company is {0}").format(company))

	if company != "IMPERIAL MEGA PRIMA":
		return

	for d in self.references:
		if d.reference_doctype == "Sales Invoice" and d.installment_no:
			si = frappe.get_doc("Sales Invoice", d.reference_name)

			for i in si.installments:
				if i.installment_no == d.installment_no:
					if self.docstatus == 1:
						i.db_set("status", "Paid")
						i.db_set("paid_date", self.posting_date)
						i.db_set("payment_ref_name", self.name)
					elif self.docstatus == 2:
						i.db_set("status", "Unpaid")
						i.db_set("paid_date", "")
						i.db_set("payment_ref_name", "") 

def imp_before_cancel_installment_payment(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	print company
	#frappe.throw(_("Company is {0}").format(company))

	if company != "IMPERIAL MEGA PRIMA":
		return

	for d in self.references:
		if d.reference_doctype == "Sales Invoice" and d.installment_no:
			si = frappe.get_doc("Sales Invoice", d.reference_name)

			for i in si.installments:
				if i.installment_no == d.installment_no:
					#if self.docstatus == 1:
					i.db_set("status", "Unpaid")
					i.db_set("paid_date", "")
					i.db_set("payment_ref_name", "")

