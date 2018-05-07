from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time
from frappe.model.naming import make_autoname
import json
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.utils import get_account_currency, get_balance_on
import erpnext.accounts.utils
from re import sub
from decimal import Decimal


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

def payment_reconciliation_onload():
	from erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation import PaymentReconciliation
	PaymentReconciliation.onload = get_outstanding_invoices_onload_pe


def item_validate(self, method):
	company = frappe.db.get_value("Global Defaults", None, "default_company") 
	#frappe.throw(_("Company is {0}").format(company))

	if company.strip().upper() not in ("SILVER PHONE","TOKO BELAKANG", "NEXTECH","HANIPET KOTEGA"):
		return
		
	self.item_code = self.item_code.strip().upper()
	self.item_name = self.item_code
	self.name = self.item_code

def si_autoname(self, method):
	frappe.message(_("Autoname Invoice No {0}").format(self.name))
	#if self.no_online_order and len(self.no_online_order) > 10:
	#	self.name = self.no_online_order

def si_on_change(self, method):
	frappe.throw(_("before_save {0}").format(self.name))
	invoice_no = frappe.db.sql('''select name from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.naming_series.strip(), as_dict=0)
	frappe.throw(cstr(invoice_no[0][0]))
	if invoice_no:
		self.name = cstr(invoice_no[0][0])

def si_before_save(self, method):
	if self.company not in ("SILVER PHONE", "TOKO BELAKANG", "NEXTECH","PT. TRIGUNA JAYA SENTOSA", "HANIPET KOTEGA"):
		return

	#frappe.msgprint(cstr(self.name))
	if self.no_online_order and len(cstr(self.no_online_order)) > 10 and self.name != self.no_online_order:
		self.name = self.no_online_order

def si_validate(self, method):
	if self.company not in ("SILVER PHONE", "TOKO BELAKANG", "NEXTECH","PT. TRIGUNA JAYA SENTOSA", "HANIPET KOTEGA"):
		return

	if self.no_online_order:
		invoice_no = frappe.db.sql('''select name from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)
	
		if invoice_no and self.no_online_order and len(cstr(self.no_online_order)) > 10:
			frappe.throw(_("Same Invoice No: {0} found").format(self.no_online_order))

def si_before_insert(self, method):
	if self.company: #make sure only import online_order
		return
	#company = frappe.db.get_value("Global Defaults", None, "default_company") 
	company = frappe.db.get_single_value('Global Defaults', 'default_company')	

	if company not in ("SILVER PHONE", "TOKO BELAKANG", "NEXTECH","PT. TRIGUNA JAYA SENTOSA", "HANIPET KOTEGA"):
		return

	same_invoice = ""
	cost_center = ""

	self.update_stock = 1
	self.company = company

	if not frappe.db.get_value("Customer", self.customer, "name"):
		frappe.throw(_("Customer {0} not found").format(self.customer))

	if self.naming_series and len(cstr(self.naming_series)) > 10:
		no_online_order = self.naming_series
		self.no_online_order = no_online_order

		if (self.is_return):
			self.name = "R-" + self.no_online_order
		else:
			self.name = self.no_online_order

	#frappe.msgprint(self.name)

	if not self.selling_price_list:
		self.selling_price_list = frappe.db.get_value("Customer", {"name":self.customer}, "default_price_list") #"Price 1"
		if not self.selling_price_list:
			self.selling_price_list = frappe.db.get_single_value('Selling Settings', 'selling_price_list')	

	self.due_date = add_days(self.posting_date, 14);


	if self.no_online_order and len(self.no_online_order) > 10:
		if (self.is_return):
			self.naming_series = "R/.no_online_order.-.##"
		else:
			self.naming_series = "no_online_order.-.##"


		#frappe.throw(_("naming_series is {0} , name is {1}").format(self.naming_series,self.name))

		for d in self.items:
			item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and item_code=%s limit 1''', (d.item_code.strip()), as_dict=0) or \
				frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
				((%s like concat (%s,item_code)) or item_name like %s or description like %s) limit 1''', 
				(d.item_code.strip(),"%",("%" + d.item_code.strip() + "%"),("%" + d.item_code.strip() + "%")), as_dict=0)
			#frappe.throw(cstr(item_code[0][0]))
			if item_code:
				d.item_code = cstr(item_code[0][0])
				d.item_name = frappe.db.get_value("Item", {"name":d.item_code}, "item_name") or d.item_code
				if not d.description:
					d.description = d.item_name

				from erpnext.stock.utils import get_stock_balance

				warehouse = frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Warehouse"}, "for_value") or \
						frappe.db.get_single_value('Stock Settings', 'default_warehouse')

				if warehouse:
					d.warehouse = warehouse
					stock_balance = get_stock_balance(d.item_code, d.warehouse, self.posting_date or nowdate(), cstr(nowtime()))
					if stock_balance <=0:
						frappe.throw(_("Insufficient Stock for item : {0}").format(d.item_code))
				else:
					frappe.throw(_("Warehouse not found for item : {0}").format(d.item_code))
			else:
				frappe.throw(_("Item Code not found : {0}").format(d.item_code))

			cost_center=frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value")
			if cost_center:
				d.cost_center = cost_center 
			else:
				d.cost_center = frappe.db.get_value("Company", company, "cost_center") 

			#remove currency symbol if any convert to float
			_rate = cstr(Decimal(sub(r'[^\d.]', '', cstr(d.rate))))
			#frappe.throw(_("rate is {0}").format(cstr(d.rate)))
			if _rate:
				d.rate = cstr(_rate).replace(".","")

		same_invoice = frappe.db.sql('''select no_online_order from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)

		if self.no_online_order and same_invoice:
			frappe.throw(_("Same Invoice No exists : {0}").format(self.no_online_order))
	else:
		frappe.throw(_("Online Order No : {0} is invalid").format(self.no_online_order or ""))

	if self.shipping_fee:
		shipping_fee = cstr(Decimal(sub(r'[^\d.]', '', cstr(self.shipping_fee))))
		self.shipping_fee = cstr(shipping_fee).replace(".","")

		insurance_fee = cstr(Decimal(sub(r'[^\d.]', '', cstr(self.insurance_fee or "0"))))
		self.insurance_fee = cstr(insurance_fee).replace(".","")

		self.taxes = {};
		account_head = frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Shipping Fee%' limit 1''', as_dict=0) or \
				frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Freight%' limit 1''', as_dict=0)
		
		self.append("taxes", {
				"charge_type": "Actual",
				"account_head": cstr(account_head[0][0]),
				"cost_center": frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value") or frappe.db.get_value("Company", company, "cost_center"),
				"description": "Ongkir",
				"tax_amount": flt(self.shipping_fee)
			})
		account_insurance = frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Insurance Fee%' limit 1''', as_dict=0)
		if self.insurance_fee and account_insurance:
			self.append("taxes", {
				"charge_type": "Actual",
				"account_head": cstr(account_insurance[0][0] if account_insurance else account_head[0][0]),
				"cost_center": frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value") or frappe.db.get_value("Company", company, "cost_center"),
				"description": "Insurance Fee",
				"tax_amount": flt(self.insurance_fee)
			})
			

def si_autoname(self, method):
	#frappe.throw(_("Series : {0}, name: {1}").format(self.naming_series, self.name))
	company = frappe.db.get_single_value('Global Defaults', 'default_company')	

	if company not in ("SILVER PHONE", "NEXTECH"):
		return

	self.update_stock = 1
	self.company = company

	if self.no_online_order and len(self.no_online_order) > 10:
		if (self.is_return):
			self.naming_series = "R/.no_online_order.-.##"
		else:
			self.naming_series = "no_online_order.-.##"

	#frappe.throw(_("Series : {0}, name: {1}").format(self.naming_series, self.name))


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


@frappe.whitelist()
def get_last_rate_by_customer(customer):
	return frappe.db.sql('''select si_item.rate from `tabSales Invoice` si join `tabSales Invoice Item` si_item on si.name=si_item.parent
		where si.docstatus=1 and customer=%s 
		and si.is_return=0 and si_item.rate > 0 order by si.posting_date desc, si.posting_time desc limit 1''', (customer), as_dict=0)

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
				{party_type} = %s and docstatus = 1 and outstanding_amount <> 0 {condition}
			order by
				posting_date, name limit 150
			""".format(
				invoice = invoice,
				party_type = scrub(party_type),
				condition=condition or ""
			), (party), as_dict = True)
	'''
	unallocated_payment_list = frappe.db.sql("""
			select
				"Payment Entry" as voucher_type, name as voucher_no,
				total_allocated_amount as invoice_amount, unallocated_amount as outstanding_amount, posting_date
			from
				`tabPayment Entry`
			where
				party_type = %s and party = %s and docstatus = 1 and unallocated_amount > 0
			order by
				posting_date, name
			""".format(
				invoice = invoice,
				party_type = scrub(party_type)
			), (party_type, party), as_dict = True)
	'''
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
	negative_outstanding_invoices = []
	if args.get("party_type") not in ["Student", "Employee"] and not args.get("voucher_no"):
		negative_outstanding_invoices = get_negative_outstanding_invoices(args.get("party_type"),
			args.get("party"), args.get("party_account"), party_account_currency, company_currency)

	# Get positive outstanding sales /purchase invoices/ Fees
	condition = ""
	if args.get("voucher_type") and args.get("voucher_no"):
		condition = " and voucher_type='{0}' and voucher_no='{1}'"\
			.format(frappe.db.escape(args["voucher_type"]), frappe.db.escape(args["voucher_no"]))

	condition = condition + " and company='{0}'".format(args.get("company"))

	outstanding_invoices = get_outstanding_invoices2(args.get("party_type"), args.get("party"),
		args.get("party_account"), condition=condition)

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
			args.get("party"), party_account_currency, company_currency,condition=condition)

	return negative_outstanding_invoices + outstanding_invoices + orders_to_be_billed

def get_orders_to_be_billed(posting_date, party_type, party, party_account_currency, company_currency,condition=None):
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
				and abs(100 - per_billed) > 0.01 {condition}
			order by
				transaction_date, name
		""".format(**{
			"ref_field": ref_field,
			"voucher_type": voucher_type,
			"party_type": scrub(party_type),
			"condition": condition
		}), party, as_dict=True)

	order_list = []
	for d in orders:
		d["voucher_type"] = voucher_type
		# This assumes that the exchange rate required is the one in the SO
		d["exchange_rate"] = get_exchange_rate(party_account_currency, company_currency, posting_date)
		order_list.append(d)

	return order_list

def get_negative_outstanding_invoices(party_type, party, party_account, party_account_currency, company_currency):
	voucher_type = "Sales Invoice" if party_type == "Customer" else "Purchase Invoice"
	if party_account_currency == company_currency:
		grand_total_field = "base_grand_total"
		rounded_total_field = "base_rounded_total"
	else:
		grand_total_field = "grand_total"
		rounded_total_field = "rounded_total"

	return frappe.db.sql("""
		select
			"{voucher_type}" as voucher_type, name as voucher_no,
			if({rounded_total_field}, {rounded_total_field}, {grand_total_field}) as invoice_amount,
			outstanding_amount, posting_date,
			due_date, conversion_rate as exchange_rate
		from
			`tab{voucher_type}`
		where
			{party_type} = %s and {party_account} = %s and docstatus = 1 and outstanding_amount < 0
		order by
			posting_date, name
		""".format(**{
			"rounded_total_field": rounded_total_field,
			"grand_total_field": grand_total_field,
			"voucher_type": voucher_type,
			"party_type": scrub(party_type),
			"party_account": "debit_to" if party_type == "Customer" else "credit_to"
		}), (party, party_account), as_dict=True)

