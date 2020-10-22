# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import msgprint, _

def execute(filters=None):
	return _execute(filters)

def _execute(filters, additional_table_columns=None, additional_query_columns=None):
	if not filters: filters = frappe._dict({})

	invoice_list = get_sales_summary(filters, additional_query_columns)
	columns = get_columns(invoice_list, additional_table_columns)

	if not invoice_list:
		msgprint(_("No record found"))
		return columns, invoice_list

	#frappe.msgprint(invoice_list)

	company_currency = frappe.db.get_value("Company", filters.get("company"), "default_currency")

	data = []
	for inv in invoice_list:
		# invoice details

		row = [
			inv.customer, inv.territory, inv.grand_total, inv.outstanding_amount
		]

		data.append(row)

	return columns, data

def get_columns(invoice_list, additional_table_columns):
	"""return columns based on filters"""
	columns = [
		_("Customer") + ":Link/Customer:120",
		_("Territory") + ":Link/Territory:120"
		#_("Qty") + ":Float:70"
	]

	columns = columns + [_("Grand Total") + ":Currency/currency:120",
		_("Outstanding Amount") + ":Currency/currency:120"]

	return columns

def get_conditions(filters):
	conditions = ""

	if filters.get("company"): conditions += " and company=%(company)s"
	if filters.get("customer"): conditions += " and customer = %(customer)s"
	if filters.get("territory"): conditions += " and territory = %(territory)s"

	if filters.get("from_date") and filters.get("to_date"): 
		conditions += " and posting_date between %(from_date)s and %(to_date)s"
	#if filters.get("to_date"): conditions += " and posting_date <= %(to_date)s"

	if filters.get("mode_of_payment"):
		conditions += """ and exists(select name from `tabSales Invoice Payment`
			 where parent=`tabSales Invoice`.name
			 	and ifnull(`tabSales Invoice Payment`.mode_of_payment, '') = %(mode_of_payment)s)"""

	return conditions

def get_sales_summary(filters, additional_query_columns):
	if additional_query_columns:
		additional_query_columns = ', ' + ', '.join(additional_query_columns)

	conditions = get_conditions(filters)
	#return frappe.db.sql("""select si.customer, si.territory, sum(si.grand_total) as grand_total, sum(si.outstanding_amount) as outstanding_amount
	#	from `tabSales Invoice` si join `tabSales Invoice Item` si_item on si.name=si_item.parent
	#	where si.docstatus = 1 %s group by si.customer, si.territory order by customer asc""" %
	#	conditions, filters, as_dict=1)

	return frappe.db.sql("""select si.customer, si.territory, sum(si.grand_total) as grand_total, sum(si.outstanding_amount) as outstanding_amount
		from `tabSales Invoice` si where si.docstatus = 1 %s group by si.customer, si.territory order by customer asc""" %
		conditions, filters, as_dict=1)

def get_invoices(filters, additional_query_columns):
	if additional_query_columns:
		additional_query_columns = ', ' + ', '.join(additional_query_columns)

	conditions = get_conditions(filters)
	return frappe.db.sql("""select name, posting_date, debit_to, project, customer, customer_name, remarks,
		base_net_total, base_grand_total, base_rounded_total, outstanding_amount {0}
		from `tabSales Invoice`
		where docstatus = 1 %s order by posting_date desc, name desc""".format(additional_query_columns or '') %
		conditions, filters, as_dict=1)

def get_invoice_income_map(invoice_list):
	income_details = frappe.db.sql("""select parent, income_account, sum(base_net_amount) as amount
		from `tabSales Invoice Item` where parent in (%s) group by parent, income_account""" %
		', '.join(['%s']*len(invoice_list)), tuple([inv.name for inv in invoice_list]), as_dict=1)

	invoice_income_map = {}
	for d in income_details:
		invoice_income_map.setdefault(d.parent, frappe._dict()).setdefault(d.income_account, [])
		invoice_income_map[d.parent][d.income_account] = flt(d.amount)

	return invoice_income_map

def get_invoice_tax_map(invoice_list, invoice_income_map, income_accounts):
	tax_details = frappe.db.sql("""select parent, account_head,
		sum(base_tax_amount_after_discount_amount) as tax_amount
		from `tabSales Taxes and Charges` where parent in (%s) group by parent, account_head""" %
		', '.join(['%s']*len(invoice_list)), tuple([inv.name for inv in invoice_list]), as_dict=1)

	invoice_tax_map = {}
	for d in tax_details:
		if d.account_head in income_accounts:
			if invoice_income_map[d.parent].has_key(d.account_head):
				invoice_income_map[d.parent][d.account_head] += flt(d.tax_amount)
			else:
				invoice_income_map[d.parent][d.account_head] = flt(d.tax_amount)
		else:
			invoice_tax_map.setdefault(d.parent, frappe._dict()).setdefault(d.account_head, [])
			invoice_tax_map[d.parent][d.account_head] = flt(d.tax_amount)

	return invoice_income_map, invoice_tax_map

def get_invoice_so_dn_map(invoice_list):
	si_items = frappe.db.sql("""select parent, sales_order, delivery_note, so_detail
		from `tabSales Invoice Item` where parent in (%s)
		and (ifnull(sales_order, '') != '' or ifnull(delivery_note, '') != '')""" %
		', '.join(['%s']*len(invoice_list)), tuple([inv.name for inv in invoice_list]), as_dict=1)

	invoice_so_dn_map = {}
	for d in si_items:
		if d.sales_order:
			invoice_so_dn_map.setdefault(d.parent, frappe._dict()).setdefault(
				"sales_order", []).append(d.sales_order)

		delivery_note_list = None
		if d.delivery_note:
			delivery_note_list = [d.delivery_note]
		elif d.sales_order:
			delivery_note_list = frappe.db.sql_list("""select distinct parent from `tabDelivery Note Item`
				where docstatus=1 and so_detail=%s""", d.so_detail)

		if delivery_note_list:
			invoice_so_dn_map.setdefault(d.parent, frappe._dict()).setdefault("delivery_note", delivery_note_list)

	return invoice_so_dn_map

def get_customer_details(customers):
	customer_map = {}
	for cust in frappe.db.sql("""select name, territory, customer_group from `tabCustomer`
		where name in (%s)""" % ", ".join(["%s"]*len(customers)), tuple(customers), as_dict=1):
			customer_map.setdefault(cust.name, cust)

	return customer_map


def get_mode_of_payments(invoice_list):
	mode_of_payments = {}
	if invoice_list:
		inv_mop = frappe.db.sql("""select parent, mode_of_payment
			from `tabSales Invoice Payment` where parent in (%s) group by parent, mode_of_payment""" %
			', '.join(['%s']*len(invoice_list)), tuple(invoice_list), as_dict=1)

		for d in inv_mop:
			mode_of_payments.setdefault(d.parent, []).append(d.mode_of_payment)

	return mode_of_payments
