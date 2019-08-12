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


def shoutout():
	print 'yay!'

def build_my_thing():
	erpnext.accounts.utils.test = shoutout

def print_test():
	test() 

def batch_autoname(self, method):
	from frappe.model.naming import make_autoname

	if frappe.db.get_value('Item', self.item, 'create_new_batch'):
		self.batch_id = make_autoname('batch-.DD.MM.YYYY.-.###', doc=self)
	elif not self.batch_id:
		frappe.throw(_('Batch ID is mandatory'), frappe.MandatoryError)

	self.name = self.batch_id
	#frappe.msgprint(_('hi {0}').format(self.name))


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

	if company.strip().upper() in ("HANIPET KOTEGA","DCENDOL SERPONG"):
		self.item_code = self.item_code.strip().upper()
		self.item_name = self.item_code
		self.name = self.item_code

	if flt(self.standard_rate) > 0:
		frappe.db.set_value("Item Price",\
				{"item_code":self.item_code,"currency":frappe.db.get_single_value('Global Defaults', 'default_currency'),\
				"selling":1,"price_list":frappe.db.get_single_value('Selling Settings', 'selling_price_list')},
				"price_list_rate",self.standard_rate)

@frappe.whitelist()
def set_si_autoname(doc, method):
	#frappe.message(_("Autoname Invoice No {0}").format(self.name))
	#if doc.company not in ("PT BLUE OCEAN LOGISTICS","PT MALABAR JAYA","PT MULTI AGUNG MANDIRI"):
	#	return
	#frappe.throw("yes")
	#if doc.company == "PT SERIMPI MEGAH PERKASA" and doc.doctype == "Payment Entry":
	#	frappe.throw("yes")
	#from frappe.model.meta import get_parent_dt

	if doc.doctype not in ("Quotation", "Sales Order", "Delivery Note","Sales Invoice","Supplier Quotation","Material Request", \
		"Purchase Order","Purchase Receipt","Purchase Invoice","Payment Entry","Journal Entry","Stock Entry","Stock Reconciliation", \
		"Request for Quotation"):
		return

	if "no_invoice" in frappe.db.get_table_columns(doc.doctype) and not doc.amended_from: # and doc.company in ("PT BLUE OCEAN LOGISTICS"):
		#if doc.no_invoice and not doc.amended_from:
		if doc.no_invoice:
			doc.name = doc.no_invoice.upper()
	
	elif "set_autoname_based_on_posting_date" in frappe.db.get_table_columns("Company") and not doc.name:
		if frappe.db.get_value("Company",doc.company,"set_autoname_based_on_posting_date"):
			if "transaction_date" in frappe.db.get_table_columns(doc.doctype):
				posting_date = doc.transaction_date
			elif "posting_date" in frappe.db.get_table_columns(doc.doctype):
				posting_date = doc.posting_date
			else:
				return

			_month = getdate(posting_date).strftime('%m')
			_year = getdate(posting_date).strftime('%y')			
			
			
			if "abbr" in frappe.db.get_table_columns("Customer") and doc.doctype == "Sales Invoice":
				abbr = frappe.db.get_value("Customer",doc.customer,"abbr")
				_series = cstr(doc.naming_series).replace("MM",_month).replace("YY",_year).replace("INV",abbr)

			else:
				_series = cstr(doc.naming_series).replace("MM",_month).replace("YY",_year)
			
			doc.name = make_autoname(_series)
	elif doc.doctype in("Purchase Invoice"):
		_month = getdate(doc.posting_date).strftime('%m')
		_year = getdate(doc.posting_date).strftime('%y')			
			
		_series = cstr(doc.naming_series).replace("MM",_month).replace("YY",_year)
			
		doc.name = make_autoname(_series)

	is_online_shop=0;
	if "is_online_shop" in frappe.db.get_table_columns("Company") and "no_online_order" in frappe.db.get_table_columns(doc.doctype):
		is_online_shop = frappe.db.get_value("Company", doc.company, "is_online_shop")

		if doc.no_online_order and len(doc.no_online_order) > 10:
			doc.name = doc.no_online_order 

	
@frappe.whitelist()
def set_pi_autoname(doc, method):
	#frappe.message(_("Autoname Invoice No {0}").format(self.name))
	if doc.company not in ("PT BLUE OCEAN LOGISTICS","PT MALABAR JAYA"):
		return

	if doc.no_invoice and not doc.amended_from:
		doc.name = doc.no_invoice.upper()
	'''
	else:
		_month = getdate(doc.posting_date).strftime('%m')
		_year = getdate(doc.posting_date).strftime('%y')
		doc.name = make_autoname("MJF-." + _year + "." + _month + ".-###")
	'''

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
	is_online_shop=0;
	if "is_online_shop" in frappe.db.get_table_columns("Company"):
		is_online_shop = frappe.db.get_value("Company", self.company, "is_online_shop")

	if not is_online_shop and self.company not in ("SILVER PHONE", "AN Electronic", "TOKO BELAKANG", "NEXTECH","PT. TRIGUNA JAYA SENTOSA", "HANIPET KOTEGA","BOMBER STORE","HIHI STORE","CENTRA ONLINE"):
		return

	if self.no_online_order:
		invoice_no = frappe.db.sql('''select name from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)
	
		if invoice_no and self.no_online_order and len(cstr(self.no_online_order)) > 10 and not self.is_return:
			frappe.throw(_("Same Invoice No: {0} found").format(self.no_online_order))

		'''Generate random AWB NO if not specified for barcode purpose'''
		if not self.awb_no and "generate_awb_barcode" in frappe.db.get_table_columns("Company") and not self.is_return:
			if frappe.db.get_value("Company", {"name":self.company}, "generate_awb_barcode"):
				temp = frappe.generate_hash()[:12].upper()
				self.awb_no = temp #+ "-" + self.no_online_order[-5:]

		for d in self.items:
			""" Get marketplace fee for official store """
			item_group = frappe.db.get_value("Item", {"name":d.item_code}, "item_group") or ""

			if item_group and frappe.db.table_exists("Marketplace Fees"):
				d.discount_percentage = frappe.db.get_value("Marketplace Fees", {"parent":item_group, "marketplace_store_name": self.customer}, "marketplace_fee_percentage") or 0.0


def validate_selling_price(it):
	last_purchase_rate, is_stock_item = frappe.db.get_value("Item", it.item_code, ["last_purchase_rate", "is_stock_item"])
	last_purchase_rate_in_sales_uom = last_purchase_rate / (it.conversion_factor or 1)
	
	if flt(it.rate) < flt(flt(last_purchase_rate_in_sales_uom) * 0.97):
		frappe.throw("Selling rate {0} is below its last purchase rate: {1}".format(cstr(it.rate), it.item_code))

	last_valuation_rate = frappe.db.sql("""
				SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
				AND warehouse = %s AND valuation_rate > 0
				ORDER BY posting_date DESC, posting_time DESC, name DESC LIMIT 1
				""", (it.item_code, it.warehouse))
	if last_valuation_rate:
		last_valuation_rate_in_sales_uom = last_valuation_rate[0][0] / (it.conversion_factor or 1)
		if is_stock_item and flt(it.rate) < flt(flt(last_valuation_rate_in_sales_uom) * 0.97):
			frappe.throw("Selling rate {0} is below its valuation rate: {1}".format(cstr(it.rate), it.item_code))

def si_before_insert(self, method):
	if self.company: #make sure only import online_order
		return
	#company = frappe.db.get_value("Global Defaults", None, "default_company") 
	company = frappe.db.get_single_value('Global Defaults', 'default_company')
	#frappe.throw(company)	

	is_online_shop=0;
	if "is_online_shop" in frappe.db.get_table_columns("Company"):
		is_online_shop = frappe.db.get_value("Company", company, "is_online_shop")

	if not is_online_shop and company not in ("PARAGON JAYA","SILVER PHONE", "AN Electronic", "TOKO BELAKANG", "NEXTECH","PT. TRIGUNA JAYA SENTOSA", "HANIPET KOTEGA","BOMBER STORE","HIHI STORE","CENTRA ONLINE"):
		return

	same_invoice = ""
	cost_center = ""

	status_order = ["BATAL","BELUM BAYAR","PENDING","UNPAID","CANCEL","MENUNGGU PEMBAYARAN"]

	if self.remarks:
		for c in status_order:
			if c in self.remarks.upper():
				frappe.throw(_("Order is either cancelled or pending for payment: {0}").format(cstr(self.no_online_order)))

	self.update_stock = 1
	self.company = company

	if not cstr(getdate(cstr(self.posting_date))):
		frappe.throw(_("Invalid date format: {0}").format(cstr(self.posting_date)))
	else:
		self.posting_time = get_time("23:59:00") or nowtime() #datetime.datetime.strptime("23:59:59", "%H:%M:%S")
		self.posting_date = cstr(getdate(cstr(self.posting_date)))


	if company in ("BOMBER STORE","CENTRA ONLINE") or "import_time" in frappe.db.get_table_columns("Sales Invoice"): #or self.import_time is not None:
		self.import_time = nowtime()	
	#elif company in ("CENTRA ONLINE"):
	#	self.posting_date = nowdate()
	#	self.import_time = nowtime()
	#	self.posting_time = nowtime()

	if not frappe.db.get_value("Customer", self.customer, "name"):
		frappe.throw(_("Customer {0} not found").format(self.customer))

	if self.naming_series and len(cstr(self.naming_series)) > 10:
		no_online_order = self.naming_series.strip()
		self.no_online_order = no_online_order

		if (self.is_return):
			self.name = "R-" + self.no_online_order
		else:
			self.name = self.no_online_order

		same_invoice = frappe.db.sql('''select no_online_order from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)
		if self.no_online_order and same_invoice:
			frappe.throw(_("Same Invoice No exists : {0}").format(self.no_online_order))


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

		if "is_official_store" in frappe.db.get_table_columns("Customer"):
			is_official_store = frappe.db.get_value("Customer", {"name":self.customer}, "is_official_store") or "0"

		for d in self.items:
			if not d.item_code:
				frappe.throw(_("Item Code is required"))
			
			#item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and item_code=%s limit 1''', (d.item_code.strip()), as_dict=0) or \
			#	frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
			#	((%s like concat (%s,item_code)) or item_name like %s or description like %s) limit 1''', 
			#	(d.item_code.strip(),"%",("%" + d.item_code.strip() + "%"),("%" + d.item_code.strip() + "%")), as_dict=0)
			
			item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and item_code=%s limit 1''', (d.item_code.strip()), as_dict=0) or \
				frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
				(item_name like %s or description like %s) limit 1''', 
				(("%" + d.item_code.strip() + "%"),("%" + d.item_code.strip() + "%")), as_dict=0)

			if item_code:
				d.item_code = cstr(item_code[0][0])
				d.item_name = frappe.db.get_value("Item", {"name":d.item_code}, "item_name") or d.item_code
				if not d.description:
					d.description = d.item_name

				from erpnext.stock.utils import get_stock_balance

				warehouse = frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Warehouse"}, "for_value") or \
						frappe.db.get_single_value('Stock Settings', 'default_warehouse')

				is_stock_item = frappe.db.get_value("Item", {"name":d.item_code}, "is_stock_item")
				if warehouse and is_stock_item:
					d.warehouse = warehouse
					stock_balance = get_stock_balance(d.item_code, d.warehouse, self.posting_date or nowdate(), self.posting_time)
					#if d.item_code == "A309PN":
					#	frappe.throw(_("Item : {0} Stock: {1} required: {2} Posting Date: {3} Posting Time: {4} Order time: {5}").format(d.item_code, cstr(stock_balance),cstr(d.qty), cstr(self.posting_date), cstr(self.posting_time), cstr(get_time(self.posting_date))))
					if (stock_balance - flt(d.qty)) < 0.0:
						frappe.throw(_("Insufficient Stock {0} > {1} for item : {2} in Warehouse {3}").format(cstr(d.qty),cstr(stock_balance),d.item_code,d.warehouse))
				else:
					if is_stock_item:
						frappe.throw(_("Warehouse not found for item : {0}").format(d.item_code))
			else:
				frappe.throw(_("Item Code not found : {0}").format(d.item_code))

			if not d.qty:
				frappe.throw(_("Qty is required for Item : {0}").format(d.item_code))

			cost_center=frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value")
			if cost_center:
				d.cost_center = cost_center 
			else:
				d.cost_center = frappe.db.get_value("Company", company, "cost_center") 

			#remove currency symbol if any convert to float
			_rate = flt(cstr(d.rate or "0").replace("Rp","").replace(".","")) #cstr(Decimal(sub(r'[^\d.]', '', cstr(d.rate or "0"))))
			_disc = 0.0

			if "discount_marketplace" in frappe.db.get_table_columns(d.doctype):
				if d.discount_marketplace:
					_disc = flt(cstr(d.discount_marketplace).replace("Rp","").replace(".",""))
					_rate = _rate + flt(_disc)
					d.discount_marketplace = flt(_disc)
					#frappe.throw(_("disc : {1}").format(cstr(_disc)))

			#if d.item_code=="CBH.CABY2.MICR.100.WHT":
			#	frappe.throw(_("rate is {0} disc {1} {2}").format(cstr(_rate), cstr(_disc), cstr(d.discount_marketplace)))
			if _rate:
				d.rate = _rate #cstr(_rate).replace(".","")
				d.price_list_rate = _rate
				if company == "BOMBER STORE":
					validate_selling_price(d)

			""" Get marketplace fee for official store """
			item_group = frappe.db.get_value("Item", {"name":d.item_code}, "item_group") or ""

			if item_group and frappe.db.table_exists("Marketplace Fees"):
				d.discount_percentage = frappe.db.get_value("Marketplace Fees", {"parent":item_group, "marketplace_store_name": self.customer}, "marketplace_fee_percentage") or 0.0
				if flt(d.discount_percentage) != 0.0:
					d.rate = flt(d.price_list_rate) * (100.0 - d.discount_percentage)/100.0


			if "total_qty" in frappe.db.get_table_columns(self.doctype):
				self.total_qty = flt(self.total_qty) + flt(d.qty)

			if "lazada_sku" in frappe.db.get_table_columns(d.doctype):
				self.shipping_fee = flt(self.shipping_fee) + flt(d.shipping_fee)
	else:
		frappe.throw(_("Online Order No : {0} is invalid").format(self.no_online_order or ""))

	'''Generate random AWB NO if not specified for barcode purpose'''
	if not self.awb_no and "generate_awb_barcode" in frappe.db.get_table_columns("Company") and not self.is_return:
		if frappe.db.get_value("Company", {"name":self.company}, "generate_awb_barcode"):
			temp = frappe.generate_hash()[:12].upper()
			self.awb_no = temp #+ "-" + self.no_online_order[-5:]
		
	if self.shipping_fee:
		shipping_fee = flt(cstr(self.shipping_fee or "0").replace("Rp","").replace(".","")) #cstr(Decimal(sub(r'[^\d.]', '', cstr(self.shipping_fee or "0"))))
		self.shipping_fee = shipping_fee #cstr(shipping_fee).replace(".","")

		insurance_fee = flt(cstr(self.insurance_fee or "0").replace("Rp","").replace(".","")) #cstr(Decimal(sub(r'[^\d.]', '', cstr(self.insurance_fee or "0"))))
		self.insurance_fee = insurance_fee #cstr(insurance_fee).replace(".","")

		self.taxes = {};
		account_head = frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Shipping Fee%' limit 1''', as_dict=0) or \
				frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Freight%' limit 1''', as_dict=0)

		no_courier = ["GOSEND","GO-SEND","GRAB","NINJA","REX","J&T", "Cepat"]

		if self.courier:
			self.courier = self.courier.upper()
		is_shipping = 1

		for c in no_courier:
			if c in self.courier:
				is_shipping = 0	
				self.shipping_fee = "0"
				if self.courier.upper() == "J&T" and self.company in ("AN Electronic") and not self.awb_no:
					is_shipping = 1
	
		if self.shipping_fee and account_head and is_shipping:
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

	'''special disc 1% for marketplace official store'''
	if "additional_discount_rate" in frappe.db.get_table_columns("Customer") and not self.is_return:
		additional_discount_rate = frappe.db.get_value("Customer", {"name":self.customer}, "additional_discount_rate")
		if flt(additional_discount_rate) > 0:
			self.apply_discount_on = "Net Total"
			self.additional_discount_percentage = flt(additional_discount_rate)
			

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
def ptmam_get_si_reference(sales_invoice, pi_no):
	return frappe.db.sql('''select si.parent,pi.supplier, case when pi.docstatus < 1 then 'Draft' else 'Submitted' End as status
		from `tabSales Invoice Reference` si, `tabPurchase Invoice` pi
		where si.parent=pi.name and pi.docstatus < 2 and si.sales_invoice_no=%s and ifnull(si.parent,'')!='' and si.parent != %s''', (sales_invoice,pi_no), as_dict=1)

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
def get_last_rate_by_customer(customer,item_code):
	return frappe.db.sql('''select si_item.rate from `tabSales Invoice` si join `tabSales Invoice Item` si_item on si.name=si_item.parent
		where si.docstatus=1 and customer like %s and item_code=%s
		and si.is_return=0 and si_item.rate > 0 order by si.posting_date desc, si.posting_time desc limit 1''', (("%" + customer + "%"),item_code), as_dict=0)

@frappe.whitelist()
def get_open_customer(customer,name):
	return frappe.db.sql('''select distinct c.name from `tabCustomer` c left join `tabSales Invoice` si on c.name=si.customer
		where si.docstatus=0 and c.disabled=0 and c.name=%s and si.name != %s limit 1''', (customer,name), as_dict=0)

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
			select distinct
				"{invoice}" as voucher_type, name as voucher_no,
				grand_total as invoice_amount, outstanding_amount, posting_date,
				due_date
			from
				`tab{invoice}`
			where
				{party_type} = %s and docstatus = 1 and outstanding_amount > 0 {condition}
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



def update_default_fiscal_year():
	d = frappe.get_doc("Global Defaults")
	if cstr(getdate(nowdate()).year) != cstr(d.current_fiscal_year):
		d.current_fiscal_year = cstr(getdate(nowdate()).year)
		d.save()


def delete_old_docs_daily1():
	old_docs = frappe.db.sql ("""SELECT name, creation FROM `tabFile` where datediff(now(),creation) > 0 and folder in ('Home/Attachments') 
		and file_name not like '%into-the-dawn%' and file_name not like '%Generate_Template%' 
		and attached_to_doctype not in ('Item') order by creation desc""", as_dict=1)

	if old_docs:
		for d in old_docs:
			frappe.delete_doc("File",d.name)
			frappe.db.commit()
	
	old_docs = frappe.db.sql ("""SELECT name, creation FROM `tabData Import`
		where datediff(now(),creation) > 0 and docstatus=0 order by creation desc""", as_dict=1)

	if old_docs:	
		for d in old_docs:
			frappe.delete_doc("Data Import",d.name)
			frappe.db.commit()

	
	frappe.db.sql ("""DELETE from `tabError Log`
		where datediff(now(),creation) > 0""")

	frappe.db.sql ("""DELETE from `tabVersion`
		where datediff(now(),creation) > 90""")

	frappe.db.sql ("""DELETE from `tabActivity Log`
		where datediff(now(),creation) > 90""")

	frappe.db.sql ("""DELETE from `tabError Snapshot`
		where datediff(now(),creation) > 0""")

	frappe.db.sql ("""DELETE from `tabDeleted Document`
		where datediff(now(),creation) > 3""")


@frappe.whitelist()
def update_print_counter1(doc, method):
	if "print" in frappe.db.get_table_columns("Sales Invoice"):
		#self.print = 1
		frappe.db.set_value("Sales Invoice",doc.name,"print",1)
		#print(ctr or 0)

def reset_default_icons():
	frappe.db.sql ("""DELETE from `tabDesktop Icon`	where module_name='Custom1'""")