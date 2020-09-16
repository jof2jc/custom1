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

@frappe.whitelist()
def get_sales_invoice_for_pick_list(doctype, txt, searchfield, start, page_len, filters):
	fields = ["name", "customer", "customer_name", "company", "awb_no", "courier"]
	fields = ", ".join(fields)

	return frappe.db.sql("""select {field} from `tabSales Invoice`
		where docstatus = 1
		order by name, customer_name
		limit %(start)s, %(page_len)s """.format(**{
			'field': fields
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

@frappe.whitelist()
def get_pick_list_items(source_name, target_doc=None):

	def update_item(source, target, source_parent):
		target.customer = source_parent.customer

	doc = get_mapped_doc("Sales Invoice", source_name, {
		"Sales Invoice": {
			"doctype": "Pick list",
			"field_no_map": [
				"date",
				"due_date"
			],
			"validation": {
				"docstatus": ["=", 0],
				"is_return": ["=", 0],
				"order_status": ["in",["To Pick","Pending"]]
			}
		},
		"Sales Invoice Item": {
			"doctype": "Pick List Item",
			"validation": {
				"is_picked": "0"
			},
			"field_map": {
				"parent": "sales_invoice",
				"name": "sales_invoice_item"
			},
			"field_no_map": [
				"sales_return_no",
				"purchase_return_no",
				"replacement_invoice",
				"picked_qty"
			],
			"postprocess": update_item,
			"condition": lambda doc: not [d for d in frappe.db.sql("""select pl_item.name from `tabPick List` pl \
				join `tabPick List Item` pl_item on pl.name=pl_item.parent \
				where pl.docstatus < 2 and pl_item.sales_invoice=%s and pl_item.sales_invoice_item=%s""", (doc.parent, doc.name), as_dict=1) if d]
		}
	}, target_doc)

	return doc


def validate_mandatory(doc):
	if not doc.marketplace_courier: return

	is_awb_mandatory = frappe.get_value("Marketplace Courier", doc.marketplace_courier, "is_awb_mandatory") or 0
	if is_awb_mandatory and not doc.awb_no:
		return 'AWB / Booking Code is mandatory for Courier "%s"' % (doc.marketplace_courier)

	return ""

def update_marketplace_return_on_sales_invoice_submit_cancel(self, method):
	if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
		if not frappe.get_value("Company", self.company,"apply_marketplace_workflow"):
			return

	meta = frappe.get_meta(self.doctype)
	if meta.has_field("awb_no") and meta.has_field("order_status") and self.docstatus == 2:
		self.order_status = "Cancelled"
		self.picked_and_packed = 0

		
		self.delivery_date = ""
		self.packing_start = ""
		self.packing_end = ""

		for d in self.items:
			d.picked_qty=0
			d.is_picked=0
			d.picked_time = ""
		

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
	if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
		if not frappe.get_value("Company", self.company,"apply_marketplace_workflow"):
			return

	meta = frappe.get_meta("Purchase Invoice Item")
	if meta.has_field("marketplace_return"):
		doc=None
		for d in self.items:
			if frappe.db.exists("Marketplace Return", d.marketplace_return):
				if not doc: doc = frappe.get_doc("Marketplace Return", d.marketplace_return)

				if doc:
					for item in doc.items:
						if item.name == d.ref_item_name and item.item_code == d.item_code and d.item_invoice == item.sales_invoice and d.sales_return_no == item.sales_return_no and d.marketplace_return == item.parent:
							if self.docstatus == 1: 
								if self.is_return and not item.purchase_return_no: 
									item.db_set("purchase_return_no",d.parent)

								elif not self.is_return and not item.purchase_invoice and item.purchase_return_no == d.purchase_return_no: 
									item.db_set("purchase_invoice",d.parent)

								item.db_set("supplier",self.supplier)
	
							elif self.docstatus == 2: 

								if self.is_return and item.purchase_return_no: 
									item.db_set("purchase_return_no","")
								elif not self.is_return and item.purchase_invoice: #and item.purchase_return_no: 
									item.db_set("purchase_invoice","")
	
							frappe.db.commit()