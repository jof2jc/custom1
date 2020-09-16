# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from six import string_types
import json
from frappe import _
from frappe.utils import nowdate, cstr, flt
from erpnext.stock.get_item_details import get_bin_details, get_default_cost_center, get_conversion_factor, get_reserved_qty_for_so
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from erpnext.stock.doctype.stock_entry.stock_entry import get_warehouse_details
from erpnext.stock.doctype.batch.batch import get_batch_no, set_batch_nos, get_batch_qty


class MarketplaceReturn(Document):
	pass


	def before_cancel(self):
		if frappe.get_list("Sales Invoice Item", fields="name", filters = [["marketplace_return","=",self.name]]) or \
			frappe.get_list("Purchase Invoice Item", fields="name", filters = [["marketplace_return","=",self.name]]):
			frappe.throw(_('Cannot cancel because document is linked with other documents. Please cancel and delete related transactions first.'))


	def validate(self):
		if self.docstatus > 0: return
		elif self.amended_from: 
			frappe.throw(_("Not allowed. Please create new Marketplace Return"))

		#if self.workflow_state == "Pending" and self.docstatus == 0: self.status == "Waiting Approval"

		for idx, d in enumerate(self.items):

			if self.docstatus == 0:
				d.sales_return_no = ""
				d.purchase_return_no = ""
				d.supplier = ""

			if not d.qty: 
				frappe.throw(_('Row %s. Qty is required' % (cstr(d.idx))))

			elif not d.sales_invoice:
				frappe.throw(_('Row %s. Sales Invoice ref is missing for Item "%s". Please use Get Items' % (cstr(d.idx), d.item_code)))

			elif frappe.get_list("Sales Invoice Item", fields="parent", filters = [["parent","=",d.sales_invoice], ["item_code","=",d.item_code], ["qty","<",d.qty]]):
				frappe.throw(_('Row %s. Return qty is bigger than in Sales Invoice %s for Item "%s"' % (cstr(d.idx), d.sales_invoice, d.item_code)))

			elif not frappe.get_list("Sales Invoice Item", fields="parent", filters = [["parent","=",d.sales_invoice], ["item_code","=",d.item_code]]):
				frappe.throw(_('Row %s. Item Code "%s" not exists in Sales Invoice "%S"' % (cstr(d.idx), d.item_code, d.sales_invoice)))
			

			#check if similar MR was made against same invoice
			docs = frappe.get_list("Marketplace Return Item", fields="parent", filters = [["parent","!=",d.parent], ["sales_invoice","=",d.sales_invoice], ["item_code","=",d.item_code]])
			if docs:
				frappe.throw(_('Row %s. Item Code "%s" and Sales Invoice "%S" is linked to another Marketplace Return No "%s"' % (cstr(d.idx), d.item_code, d.sales_invoice, docs[0].parent)))


			is_serial = frappe.db.get_value("Item", d.item_code, "has_serial_no") or 0
			is_batch = frappe.db.get_value("Item", d.item_code, "has_batch_no") or 0

			if is_serial:
				if not d.serial_no.strip():
					frappe.throw(_('Row %s. Serial No is required for Item "%s"' % (cstr(d.idx), d.item_code)))
				elif not is_batch and d.batch_no: 
					frappe.msgprint(_('Row %s. Item "%s" should not has batch. Removed Batch No' % (cstr(d.idx), d.item_code)))
					d.batch_no = ""

				serial_list=[]
				serial_list = d.serial_no.strip().split("\n")
				if d.qty != len(serial_list):
					frappe.throw(_('Row %s. Qty is not equal with Serial Nos qty' % (cstr(d.idx))))

				for s in serial_list:
					if not frappe.get_list("Sales Invoice Item", fields="parent", filters = [["parent","=",d.sales_invoice], ["item_code","=",d.item_code],["serial_no","like","%s" % ('%' + s + '%')]]):
						frappe.throw(_('Row %s. Serial "%s" not exists in Sales Invoice "%S"' % (cstr(d.idx), s, d.sales_invoice)))
					elif frappe.get_list("Serial No", fields="name", filters = [["name","=",s],["delivery_document_no","=",""]]):
						frappe.throw(_('Row %s. Sales Return cannot be made against Serial "%s". Status: Active' % (cstr(d.idx), s)))
					elif not frappe.get_list("Serial No", fields="name", filters = [["name","=",s], ["item_code", "=", d.item_code]]): 
						frappe.throw(_('Row %s. Item "%S" has no Serial "%s". Status: Not exists' % (cstr(d.idx), d.item_code, s)))

			if is_batch:
				if not d.batch_no.strip():
					frappe.throw(_('Row %s. Batch No is required for Item "%s"' % (cstr(d.idx), d.item_code)))
				elif not is_serial and d.serial_no: 
					frappe.msgprint(_('Row %s. Item "%s" should not has serial. Removed Serial Nos' % (cstr(d.idx), d.item_code)))
					d.serial_no = ""

				if not frappe.get_list("Sales Invoice Item", fields="parent", filters = [["parent","=",d.sales_invoice], ["item_code","=",d.item_code],["batch_no","=",d.batch_no]]):
					frappe.throw(_('Row %s. Batch "%s" not exists in Sales Invoice "%S"' % (cstr(d.idx), d.batch_no, d.sales_invoice)))

				batch_id = frappe.db.get_value("Batch", {"name":d.batch_no, "disabled":0}, "batch_id") or ""
				if not batch_id:
					frappe.throw(_('Row %s. Return cannot be made against Batch "%s". Status: Disabled / Not Exists' % (cstr(d.idx), d.batch_no)))

			if d.item_code:
				if d.serial_no and not is_serial:
					frappe.throw(_('Row %s. Item "%s" should not has serial' % (cstr(d.idx), d.item_code)))
				elif d.batch_no and not is_batch: 
					frappe.throw(_('Row %s. Item "%s" should not has batch' % (cstr(d.idx), d.item_code)))


	def get_item_details(self, args=None, for_update=False):
		item = frappe.db.sql("""select i.name, i.stock_uom, i.description, i.image, i.item_name, i.item_group,
				i.has_batch_no, i.has_serial_no,
				id.expense_account, id.buying_cost_center, id.income_account
			from `tabItem` i LEFT JOIN `tabItem Default` id ON i.name=id.parent and id.company=%s
			where i.name=%s
				and i.disabled=0
				and (i.end_of_life is null or i.end_of_life='0000-00-00' or i.end_of_life > %s)""",
			(self.company, args.get('item_code'), nowdate()), as_dict = 1)

		if not item:
			frappe.throw(_("Item {0} is not active or end of life has been reached").format(args.get("item_code")))

		item = item[0]
		item_group_defaults = get_item_group_defaults(item.name, self.company)
		brand_defaults = get_brand_defaults(item.name, self.company)

		ret = frappe._dict({
			'item_code'			: item.name,
			'uom'			      	: item.stock_uom,
			'stock_uom'			: item.stock_uom,
			'description'		  	: item.description,
			'image'				: item.image,
			'item_name' 		  	: item.item_name,
			'cost_center'			: get_default_cost_center(args, item, item_group_defaults, brand_defaults, self.company),
			'qty'				: args.get("qty") or 1,
			'batch_no'			: '',
			'actual_qty'			: 0,
			'serial_no'			: '',
			'has_serial_no'			: item.has_serial_no or 0,
			'has_batch_no'			: item.has_batch_no or 0,
			'expense_account'		: item.expense_account or '',
			'income_account'		: item.income_account or '',
		})
		
		if not ret["expense_account"]:
			ret["expense_account"] = (item.get("expense_account") or
				item_group_defaults.get("expense_account") or
				frappe.get_cached_value('Company',  self.company,  "default_expense_account"))

		if not ret["income_account"]:
			ret["income_account"] = (item.get("income_account") or
				item_group_defaults.get("income_account") or
				frappe.get_cached_value('Company',  self.company,  "default_income_account"))

		for company_field, field in {'stock_adjustment_account': 'expense_account',
			'cost_center': 'cost_center'}.items():
			if not ret.get(field):
				ret[field] = frappe.get_cached_value('Company',  self.company,  company_field)

		stock_and_rate = get_warehouse_details(args) if args.get('warehouse') else {}
		ret.update(stock_and_rate)

		# automatically select batch for outgoing item
		if (args.get('warehouse', None) and ret.get('qty') and
			ret.get('has_batch_no') and not args.get('batch_no')):
			ret["batch_no"] = get_batch_no(args['item_code'], args['warehouse'], args.get('qty'))
		

		return ret


@frappe.whitelist()
def make_new_purchase_invoice(source_name, for_supplier=None, selected_items=[], target_doc=None):
	if isinstance(selected_items, string_types):
		selected_items = json.loads(selected_items)

	def set_missing_values(source, target):
		target.supplier = for_supplier
		target.is_return = 0

	def update_item(source, target, source_parent):
		if target.qty < 0: target.qty = target.qty * -1

	suppliers =[]
	if for_supplier:
		suppliers.append(for_supplier)

	if not suppliers:
		frappe.throw(_("Please set a Supplier against Selected Items."))

	for supplier in suppliers:
		si =frappe.get_list("Purchase Invoice", filters={"marketplace_return":source_name, "supplier":supplier, "docstatus": (">", "2")})
		if len(si) == 0:
			doc = get_mapped_doc("Marketplace Return", source_name, {
				"Marketplace Return": {
					"doctype": "Purchase Invoice",
					"field_no_map": [
						"posting_date",
						"status"
					],
					"validation": {
						"docstatus": ["=", 1]
					}
				},
				"Marketplace Return Item": {
					"doctype": "Purchase Invoice Item",
					"field_map":  [
						["name", "ref_item_name"],
						["parent", "marketplace_return"],
						["sales_return_no", "sale_return_no"],
						["sales_invoice", "item_invoice"],
						["purchase_return_no", "purchase_return_no"],
						["batch_no","batch_no"],
						["serial_no","serial_no"]
			 		],
					"field_no_map": [
						"rate",
						"price_list_rate"
					],
					"postprocess": update_item,
					"condition": lambda doc: doc.item_code in selected_items and doc.sales_return_no and doc.purchase_return_no and not doc.purchase_invoice
				}
			}, target_doc, set_missing_values)
		else:
			suppliers =[]
	if suppliers:
		return doc
	else:
		frappe.msgprint(_("New Purchase Invoice already created for selected items"))

@frappe.whitelist()
def make_purchase_return(source_name, for_supplier=None, selected_items=[], target_doc=None):
	if isinstance(selected_items, string_types):
		selected_items = json.loads(selected_items)

	def set_missing_values(source, target):
		target.supplier = for_supplier
		target.is_return = 1

	def update_item(source, target, source_parent):
		if target.qty: target.qty = target.qty * -1

	suppliers =[]
	if for_supplier:
		suppliers.append(for_supplier)

	if not suppliers:
		frappe.throw(_("Please set a Supplier against Selected Items."))

	for supplier in suppliers:
		si =frappe.get_list("Purchase Invoice", filters={"marketplace_return":source_name, "supplier":supplier, "docstatus": (">", "2")})
		if len(si) == 0:
			doc = get_mapped_doc("Marketplace Return", source_name, {
				"Marketplace Return": {
					"doctype": "Purchase Invoice",
					"field_no_map": [
						"posting_date",
						"status"
					],
					"validation": {
						"docstatus": ["<=", 1]
					}
				},
				"Marketplace Return Item": {
					"doctype": "Purchase Invoice Item",
					"field_map":  [
						["name", "ref_item_name"],
						["parent", "marketplace_return"],
						["sales_return_no", "sale_return_no"],
						["sales_invoice", "item_invoice"],
						["batch_no","batch_no"],
						["serial_no","serial_no"]
			 		],
					"field_no_map": [
						"rate",
						"price_list_rate"
					],
					"postprocess": update_item,
					"condition": lambda doc: doc.item_code in selected_items and doc.sales_return_no and not doc.purchase_return_no
				}
			}, target_doc, set_missing_values)
		else:
			suppliers =[]
	if suppliers:
		return doc
	else:
		frappe.msgprint(_("Purchase Return already created for selected items"))


@frappe.whitelist()
def make_sales_return(source_name, for_customer=None, selected_items=[], target_doc=None):
	if isinstance(selected_items, string_types):
		selected_items = json.loads(selected_items)

	def set_missing_values(source, target):
		target.customer = for_customer
		target.is_return = 1

	def update_item(source, target, source_parent):
		if target.qty: target.qty = target.qty * -1

	customers =[]
	if for_customer:
		customers.append(for_customer)

	if not customers:
		frappe.throw(_("Please set a Customer against Selected Items."))

	for customer in customers:
		si =frappe.get_list("Sales Invoice", filters={"marketplace_return":source_name, "customer":customer, "docstatus": (">", "2")})
		if len(si) == 0:
			doc = get_mapped_doc("Marketplace Return", source_name, {
				"Marketplace Return": {
					"doctype": "Sales Invoice",
					"field_no_map": [
						"posting_date",
						"status"
					],
					"validation": {
						"docstatus": ["<=", 1]
					}
				},
				"Marketplace Return Item": {
					"doctype": "Sales Invoice Item",
					"field_map":  [
						["name", "ref_item_name"],
						["parent", "marketplace_return"],
						["sales_invoice", "item_invoice"],
						["batch_no","batch_no"],
						["serial_no","serial_no"]
			 		],
					"field_no_map": [
						#"rate",
						"price_list_rate"
					],
					"postprocess": update_item,
					"condition": lambda doc: doc.item_code in selected_items and not doc.sales_return_no
				}
			}, target_doc, set_missing_values)
		else:
			customers =[]
	if customers:
		return doc
	else:
		frappe.msgprint(_("sales Return already created for this Customer"))


@frappe.whitelist()
def make_replacement_invoice(source_name, sales_invoice=None, selected_items=[], target_doc=None):
	if isinstance(selected_items, string_types):
		selected_items = json.loads(selected_items)

	def set_missing_values(source, target):
		if sales_invoice:
			inv = frappe.get_doc("Sales Invoice", sales_invoice)
			target.is_replacement = 1
			target.customer = inv.customer
			target.no_online_order = "REPL/" + sales_invoice
			target.recipient = inv.recipient
			target.recipient_number = inv.recipient_number
			target.ship_to = inv.ship_to
			target.order_status = "To Pick"

	def update_item(source, target, source_parent):
		target.no_online_order = "REPL/" + source.sales_invoice

	sales_invoices =[]
	if sales_invoice:
		sales_invoices.append(sales_invoice)

	if not sales_invoices:
		frappe.throw(_("Please select a Sales Invoice for Selected Items."))

	for si in sales_invoices:
		si =frappe.get_list("Sales Invoice", filters={"marketplace_return":source_name, "item_invoice":si,"is_replacement":1, "docstatus": ("<", "2")})
		if len(si) == 0:
			doc = get_mapped_doc("Marketplace Return", source_name, {
				"Marketplace Return": {
					"doctype": "Sales Invoice",
					"field_no_map": [
						"posting_date",
						"status"
					],
					"validation": {
						"docstatus": ["<=", 1]
					}
				},
				"Marketplace Return Item": {
					"doctype": "Sales Invoice Item",
					"field_map":  [
						["name", "ref_item_name"],
						["parent", "marketplace_return"],
						["sales_invoice", "item_invoice"],
						["batch_no","batch_no"],
						["serial_no","serial_no"]
			 		],
					"field_no_map": [
						#"rate",
						"price_list_rate"
					],
					#"postprocess": update_item,
					"condition": lambda doc: doc.item_code in selected_items and doc.sales_return_no and not doc.replacement_invoice
				}
			}, target_doc, set_missing_values)
		else:
			sales_invoices =[]
	if sales_invoices:
		return doc
	else:
		frappe.msgprint(_("Replacement Invoice already created for this Sales Invoice"))


@frappe.whitelist()
def get_sales_invoice_items(source_name, target_doc=None):
	ref_items = []
	ref_doc=None

	if isinstance(target_doc, string_types):
		ref_doc = frappe.get_doc(json.loads(target_doc))

		#if ref_doc:
		#	for d in ref_doc.items:
		#		ref_items.append(d)
	'''
	if isinstance(ref_items, string_types) and ref_items:
		ref_items = json.loads(ref_items)
	'''

	def update_item(source, target, source_parent):
		target.customer = source_parent.customer

	doc = get_mapped_doc("Sales Invoice", source_name, {
		"Sales Invoice": {
			"doctype": "Marketplace Return",
			"field_no_map": [
				"customer",
				"date"
			],
			"validation": {
				"docstatus": ["=", 1],
				"is_return": ["=", 0]
			}
		},
		"Sales Invoice Item": {
			"doctype": "Marketplace Return Item",
			"field_map": {
				"batch_no": "batch_no",
				"serial_no": "serial_no"
			},
			"field_no_map": [
				"sales_return_no",
				"purchase_return_no",
				"replacement_invoice"
			],
			"postprocess": update_item,
			"condition": lambda doc: not [d for d in frappe.db.sql("""select mr.name from `tabMarketplace Return` mr \
				join `tabMarketplace Return Item` mr_item on mr.name=mr_item.parent \
				where mr.docstatus < 2 and mr_item.sales_invoice=%s and mr_item.item_code=%s""", (doc.parent, doc.item_code), as_dict=1) if d]
			#"condition": lambda doc: not [d for d in ref_items if d.sales_invoice == doc.parent and d.item_code == doc.item_code]
		}
	}, target_doc)

	return doc


@frappe.whitelist()
def get_customer(doctype, txt, searchfield, start, page_len, filters):
	fields = ["name", "customer_name", "customer_group"]
	fields = ", ".join(fields)

	return frappe.db.sql("""select {field} from `tabCustomer`
		where docstatus < 2
			and ({key} like %(txt)s
				or customer_name like %(txt)s)
			and name in (select mret.customer from `tabMarketplace Return Item` mret where mret.parent = %(parent)s)
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, customer_name), locate(%(_txt)s, customer_name), 99999),
			name, customer_name
		limit %(start)s, %(page_len)s """.format(**{
			'field': fields,
			'key': frappe.db.escape(searchfield)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len,
			'parent': filters.get('parent')
		})

@frappe.whitelist()
def get_supplier(doctype, txt, searchfield, start, page_len, filters):
	fields = ["name", "supplier_name"]
	fields = ", ".join(fields)

	return frappe.db.sql("""select {field} from `tabSupplier`
		where docstatus < 2
			and ({key} like %(txt)s
				or supplier_name like %(txt)s)
			and name in (select mret.supplier from `tabMarketplace Return Item` mret where mret.parent = %(parent)s)
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, supplier_name), locate(%(_txt)s, supplier_name), 99999),
			name, supplier_name
		limit %(start)s, %(page_len)s """.format(**{
			'field': fields,
			'key': frappe.db.escape(searchfield)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len,
			'parent': filters.get('parent')
		})

@frappe.whitelist()
def get_sales_invoice(doctype, txt, searchfield, start, page_len, filters):
	fields = ["name", "customer", "customer_name", "awb_no", "recipient", "courier"]
	fields = ", ".join(fields)

	return frappe.db.sql("""select {field} from `tabSales Invoice`
		where docstatus = 1
			and ({key} like %(txt)s
				or name like %(txt)s)
			and name in (select mret.sales_invoice from `tabMarketplace Return Item` mret where mret.parent = %(parent)s)
		order by
			if(locate(%(_txt)s, name), locate(%(_txt)s, name), 99999),
			if(locate(%(_txt)s, customer_name), locate(%(_txt)s, customer_name), 99999),
			name, customer_name
		limit %(start)s, %(page_len)s """.format(**{
			'field': fields,
			'key': frappe.db.escape(searchfield)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len,
			'parent': filters.get('parent')
		})