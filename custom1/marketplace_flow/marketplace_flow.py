from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time
from frappe.utils.dateutils import parse_date
from frappe.model.naming import make_autoname
import json
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.utils import get_account_currency, get_balance_on
import erpnext.accounts.utils
from re import sub
from decimal import Decimal
from frappe.model.mapper import get_mapped_doc


def update_marketplace_return_on_sales_invoice_submit_cancel(self, method):
	meta = frappe.get_meta(self.doctype)
	if meta.has_field("awb_no") and meta.has_field("order_status") and self.docstatus == 2:
		self.order_status = "Cancelled"
		self.picked_and_packed = 0

	meta = frappe.get_meta("Sales Invoice Item")
	if meta.has_field("marketplace_return") and self.is_return:
		doc=None
		for d in self.items:
			if frappe.db.exists("Marketplace Return", d.marketplace_return):
				if not doc: doc = frappe.get_doc("Marketplace Return", d.marketplace_return)

				if doc:
					for item in doc.items:
						if item.name == d.ref_item_name and item.item_code == d.item_code and d.item_invoice == item.sales_invoice and d.marketplace_return == item.parent:
							if self.docstatus == 1 and not item.sales_return_no: 
								item.db_set("sales_return_no",d.parent)
								item.db_set("batch_no",d.batch_no)
								item.db_set("serial_no",d.serial_no)
								item.db_set("qty", d.qty * -1)

							elif self.docstatus == 2 and item.sales_return_no: item.db_set("sales_return_no","")

							frappe.db.commit()

	meta = frappe.get_meta(self.doctype)
	if meta.has_field("is_replacement") and not self.is_return:
		if not self.is_replacement: return

		for d in self.items:
			if frappe.db.exists("Marketplace Return", d.marketplace_return):
				if not doc: doc = frappe.get_doc("Marketplace Return", d.marketplace_return)

				if doc:
					for item in doc.items:
						if item.name == d.ref_item_name and item.item_code == d.item_code and d.item_invoice == item.sales_invoice and d.marketplace_return == item.parent:
							if self.docstatus == 1 and not item.replacement_invoice: 
								item.db_set("replacement_invoice",d.parent)

							elif self.docstatus == 2 and item.replacement_invoice: 
								item.db_set("replacement_invoice","")

							frappe.db.commit()
			



def update_marketplace_return_on_purchase_invoice_submit_cancel(self, method):
	meta = frappe.get_meta("Purchase Invoice Item")
	if meta.has_field("marketplace_return") and self.is_return:
		doc=None
		for d in self.items:
			if frappe.db.exists("Marketplace Return", d.marketplace_return):
				if not doc: doc = frappe.get_doc("Marketplace Return", d.marketplace_return)

				if doc:
					for item in doc.items:
						if item.name == d.ref_item_name and item.item_code == d.item_code and d.item_invoice == item.sales_invoice and d.sales_return_no == item.sales_return_no and d.marketplace_return == item.parent:
							if self.docstatus == 1 and not item.purchase_return_no: 
								item.db_set("purchase_return_no",d.parent)
								item.db_set("supplier",self.supplier)
	
							elif self.docstatus == 2 and item.purchase_return_no: item.db_set("purchase_return_no","")
	
							frappe.db.commit()