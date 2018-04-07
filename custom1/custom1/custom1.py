from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate
from frappe.model.naming import make_autoname
import json
import datetime
from erpnext.accounts.utils import get_account_currency
import erpnext.accounts.utils

def shoutout():
	print 'yay!'

def build_my_thing():
	erpnext.accounts.utils.test = shoutout

def print_test():
	test() 

@frappe.whitelist()
def get_outstanding_invoices_onload_pe(self=None, method=None):
	import erpnext.accounts.utils
	erpnext.accounts.utils.get_outstanding_invoices = get_outstanding_invoices2


def item_validate(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	#frappe.throw(_("Company is {0}").format(company))

	if company.strip().upper() not in ("SILVER PHONE","TOKO BELAKANG", "NEXTECH"):
		return
		
	self.item_code = self.item_code.strip().upper()
	self.item_name = self.item_code
	self.name = self.item_code

def si_validate(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 

	if company not in ("SILVER PHONE","TOKO BELAKANG", "NEXTECH"):
		return

	sames_invoice = ""

	self.update_stock = 1
	self.company = company

	if not self.selling_price_list:
		self.selling_price_list = cost_center=frappe.db.get_value("Customer", {"name":self.customer}, "default_price_list") #"Price 1"

	self.due_date = add_days(self.posting_date, 7);

	#frappe.throw(_("Company is {0}").format(company))

	if self.no_online_order and len(self.no_online_order) > 5:
		if (self.is_return):
			self.naming_series = "R/.no_online_order.-.##"
		else:
			self.naming_series = "no_online_order.-.##"

		for d in self.items:
			cost_center=frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value")
			if cost_center:
				d.cost_center = cost_center 
			else:
				d.cost_center = frappe.db.get_value("Company", company, "cost_center") 

		same_invoice = frappe.db.sql('''select no_online_order from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)

	if self.no_online_order and same_invoice:
		frappe.throw(_("Same Invoice No exists : {0}").format(self.no_online_order))

def si_autoname(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	print company
	#frappe.throw(_("Company is {0}").format(company))

	if company != "NEXTECH":
		return

	if not self.name:
		self.name = self.no_online_order.strip().upper()

@frappe.whitelist()
def nex_get_invoice_by_orderid(order_id, customer):
	return frappe.db.sql('''select si.name, si.outstanding_amount from `tabSales Invoice` si
		where si.name like %s and si.docstatus=1 and si.outstanding_amount > 0 and customer=%s 
		and si.is_return=0 limit 1''', (("%" + order_id.strip() + "%"),customer), as_dict=0)


@frappe.whitelist()
def an_get_invoice_by_orderid(order_id, customer):
	return frappe.db.sql('''select si.name, si.outstanding_amount from `tabSales Invoice` si
		where (si.remarks like %s or si.no_online_order like %s or si.name like %s) and si.docstatus=1 and si.outstanding_amount > 0 and customer=%s 
		and si.is_return=0 limit 1''', (("%" + order_id.strip() + "%"),("%" + order_id.strip() + "%"),("%" + order_id.strip() + "%"),customer), as_dict=0)


def get_outstanding_invoices2(party_type, party, account, condition=None):
	outstanding_invoices = []
	precision = frappe.get_precision("Sales Invoice", "outstanding_amount")

	if party_type=="Customer":
		dr_or_cr = "debit_in_account_currency - credit_in_account_currency"
		payment_dr_or_cr = "payment_gl_entry.credit_in_account_currency - payment_gl_entry.debit_in_account_currency"
	else:
		dr_or_cr = "credit_in_account_currency - debit_in_account_currency"
		payment_dr_or_cr = "payment_gl_entry.debit_in_account_currency - payment_gl_entry.credit_in_account_currency"

	invoice = 'Sales Invoice' if party_type == 'Customer' else 'Purchase Invoice'

	invoice_list = frappe.db.sql("""
			select
				"{invoice}" as voucher_type, name as voucher_no,
				grand_total as invoice_amount, outstanding_amount, posting_date,
				due_date
			from
				`tab{invoice}`
			where
				{party_type} = %s and docstatus = 1 and outstanding_amount > 0
			order by
				posting_date, name
			""".format(
				invoice = invoice,
				party_type = scrub(party_type)
			), (party), as_dict = True)

	

	for d in invoice_list:
		outstanding_invoices.append(frappe._dict({
			'voucher_no': d.voucher_no,
			'voucher_type': d.voucher_type,
			'due_date': d.due_date,
			'posting_date': d.posting_date,
			'invoice_amount': flt(d.invoice_amount),
			'payment_amount': flt(d.invoice_amount - d.outstanding_amount, precision),
			'outstanding_amount': flt(d.outstanding_amount),
			'due_date': frappe.db.get_value(d.voucher_type, d.voucher_no, 
				"posting_date" if party_type=="Employee" else "due_date"),
		}))



	outstanding_invoices = sorted(outstanding_invoices, key=lambda k: k['due_date'] or getdate(nowdate()))

	return outstanding_invoices

@frappe.whitelist()
def get_outstanding_reference_documents2(args):
	if isinstance(args, basestring):
		args = json.loads(args)

	party_account_currency = get_account_currency(args.get("party_account"))
	company_currency = frappe.db.get_value("Company", args.get("company"), "default_currency")

	# Get negative outstanding sales /purchase invoices
	total_field = "base_grand_total" if party_account_currency == company_currency else "grand_total"

	negative_outstanding_invoices = []
	if (args.get("party_type") != "Student"):
		negative_outstanding_invoices = get_negative_outstanding_invoices(args.get("party_type"),
			args.get("party"), args.get("party_account"), total_field)

	# Get positive outstanding sales /purchase invoices/ Fees
	outstanding_invoices = get_outstanding_invoices2(args.get("party_type"), args.get("party"),
		args.get("party_account"))

	for d in outstanding_invoices:
		d["exchange_rate"] = 1
		if party_account_currency != company_currency:
			if d.voucher_type in ("Sales Invoice", "Purchase Invoice", "Expense Claim"):
				d["exchange_rate"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "conversion_rate")
			elif d.voucher_type == "Journal Entry":
				d["exchange_rate"] = get_exchange_rate(
					party_account_currency,	company_currency, d.posting_date
				)
		if d.voucher_type in ("Purchase Invoice"):
			d["bill_no"] = frappe.db.get_value(d.voucher_type, d.voucher_no, "bill_no")

	# Get all SO / PO which are not fully billed or aginst which full advance not paid
	orders_to_be_billed = []
	if (args.get("party_type") != "Student"):
		orders_to_be_billed =  get_orders_to_be_billed(args.get("posting_date"),args.get("party_type"),
			args.get("party"), party_account_currency, company_currency)

	return negative_outstanding_invoices + outstanding_invoices + orders_to_be_billed

def get_orders_to_be_billed(posting_date, party_type, party, party_account_currency, company_currency):
	if party_type == "Customer":
		voucher_type = 'Sales Order'
	elif party_type == "Supplier":
		voucher_type = 'Purchase Order'
	elif party_type == "Employee":
		voucher_type = None

	orders = []
	if voucher_type:
		ref_field = "base_grand_total" if party_account_currency == company_currency else "grand_total"

		orders = frappe.db.sql("""
			select
				name as voucher_no,
				{ref_field} as invoice_amount,
				({ref_field} - advance_paid) as outstanding_amount,
				transaction_date as posting_date
			from
				`tab{voucher_type}`
			where
				{party_type} = %s
				and docstatus = 1
				and ifnull(status, "") != "Closed"
				and {ref_field} > advance_paid
				and abs(100 - per_billed) > 0.01
			order by
				transaction_date, name
			""".format(**{
				"ref_field": ref_field,
				"voucher_type": voucher_type,
				"party_type": scrub(party_type)
			}), party, as_dict = True)

	order_list = []
	for d in orders:
		d["voucher_type"] = voucher_type
		# This assumes that the exchange rate required is the one in the SO
		d["exchange_rate"] = get_exchange_rate(party_account_currency,
			company_currency, posting_date)
		order_list.append(d)

	return order_list

def get_negative_outstanding_invoices(party_type, party, party_account, total_field):
	if party_type != "Employee":
		voucher_type = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
		return frappe.db.sql("""
			select
				"{voucher_type}" as voucher_type, name as voucher_no,
				{total_field} as invoice_amount, outstanding_amount, posting_date,
				due_date, conversion_rate as exchange_rate
			from
				`tab{voucher_type}`
			where
				{party_type} = %s and {party_account} = %s and docstatus = 1 and outstanding_amount < 0
			order by
				posting_date, name
			""".format(**{
				"total_field": total_field,
				"voucher_type": voucher_type,
				"party_type": scrub(party_type),
				"party_account": "debit_to" if party_type=="Customer" else "credit_to"
			}), (party, party_account), as_dict = True)
	else:
		return []

