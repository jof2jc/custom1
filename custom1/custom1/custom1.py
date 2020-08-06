from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time, get_site_name, time_diff_in_hours
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

#def shoutout():
#print 'yay!'

#def build_my_thing():
#erpnext.accounts.utils.test = shoutout

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
		"Request for Quotation","Billing Receipt"):
		return

	if "no_invoice" in frappe.db.get_table_columns(doc.doctype) and not doc.amended_from: # and doc.company in ("PT BLUE OCEAN LOGISTICS"):
		#if doc.no_invoice and not doc.amended_from:
		if doc.no_invoice:
			doc.name = doc.no_invoice.upper()
			return
	
	if "set_autoname_based_on_posting_date" in frappe.db.get_table_columns("Company") and not doc.name:
		if doc.doctype in ("Purchase Receipt"):
			if doc.supplier_delivery_note:	
				_series = doc.supplier_delivery_note + "-" + doc.naming_series	
				doc.name = make_autoname(_series)
				return

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

	elif doc.doctype in("Stock Entry"):
		if "phase" in frappe.db.get_table_columns(doc.doctype) and "awb_no" in frappe.db.get_table_columns(doc.doctype) and not doc.amended_from: 
			if doc.phase:
				prev_awb = frappe.db.sql('''select name from `tabStock Entry` where docstatus=1 and awb_no=%s and phase='New Order' order by creation desc limit 1''', doc.awb_no, as_dict=0)

				if prev_awb and doc.phase == "New Order":
					frappe.throw("New Order error. Same AWB No is found")
					prev_awb=None

				prev_awb = frappe.db.sql('''select name from `tabStock Entry` where docstatus=1 and awb_no=%s and phase=%s order by creation desc limit 1''', (doc.awb_no,doc.phase), as_dict=0)

				if prev_awb and doc.awb_no:
					frappe.throw("Stage: " + doc.phase + ". Same AWB No is found")

				_month = getdate(doc.posting_date).strftime('%m')
				_year = getdate(doc.posting_date).strftime('%y')

				if doc.awb_no:
					doc.name = make_autoname(doc.awb_no + "-" + doc.phase + "-." + _year + "." + _month + ".-.##")
					doc.title = doc.awb_no + "-" + doc.phase
				else:
					doc.name = make_autoname(doc.phase + "-." + _year + "." + _month + ".-.##")
					doc.title = doc.phase
				
				return

	is_online_shop=0;
	if "is_online_shop" in frappe.db.get_table_columns("Company") and "no_online_order" in frappe.db.get_table_columns(doc.doctype):
		is_online_shop = frappe.db.get_value("Company", doc.company, "is_online_shop")

		if doc.no_online_order and len(cstr(doc.no_online_order)) >= 10:
			if not doc.is_return:
				doc.name = doc.no_online_order 
			else:
				doc.name = "R/" + doc.no_online_order
	
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

def si_after_save(self, method):
	#controller to validate user when change order_status manually
	meta = frappe.get_meta(self.doctype)
	if meta.has_field("awb_no") and meta.has_field("order_status"):
		if not frappe.db.exists(self.doctype,{"name":self.name, "docstatus":0, "is_return":0}): return

		if not self.no_online_order: #skip if not-online_order
			self.order_status = ""
			return 

		apply_marketplace_workflow = 0
		if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
			apply_marketplace_workflow = frappe.get_value("Company", self.company,"apply_marketplace_workflow") or 0
			if not apply_marketplace_workflow:
				return

		if self.order_status == "To Pack": 
			if frappe.db.get_values("Sales Invoice Item", {"parent":self.name,"is_picked":"0"},"item_code"):
				self.db_set("order_status","To Pick")
				frappe.msgprint(_("Not picked items found. Changed order status = To Pick"))
	
		elif self.order_status == "Completed": 
			if self.docstatus != 1 and not self.packing_end:
				frappe.throw(_("Please make sure Pick and Pack is done properly. Cannot change to Completed manually"))

		elif self.order_status == "Cancelled": 
			frappe.msgprint(_("Warning. If you change order status to Cancelled then you will not be able to continue"))
		
		elif self.no_online_order and self.awb_no and not self.order_status: 
			frappe.throw(_("Order Status cannot be blank"))

		#doc = frappe.get_doc("Sales Invoice", self.name)
		for d in self.items:
			if apply_marketplace_workflow and ((d.is_picked and d.qty != d.picked_qty) or (d.qty < d.picked_qty and d.qty != 0)):
				d.is_picked=0
				frappe.throw(_("Please make sure Picked Qty is equal with Order Qty before change Is_Picked. Item: {0}".format(d.item_code)))

		if self.order_status == "To Pick": 
			if not frappe.db.get_values("Sales Invoice Item", {"parent":self.name,"is_picked":"0"},"item_code"):
				self.db_set("order_status","To Pack")
				frappe.msgprint(_("All items are picked already. Changed order status = To Pack"))


			
def calculate_mp_seller_discount(self):
	total_seller_discount = seller_discount_per_item = 0

	if "seller_discount" in frappe.db.get_table_columns(self.doctype) and "seller_voucher" in frappe.db.get_table_columns(self.doctype):
		if self.seller_discount and not flt(cstr(self.seller_discount)):
			self.seller_discount = flt(cstr(self.seller_discount or "0").replace("Rp","").replace(".",""))
			total_seller_discount = total_seller_discount + self.seller_discount or 0.0

		if self.seller_voucher and not flt(cstr(self.seller_voucher)):
			self.seller_voucher = flt(cstr(self.seller_voucher or "0").replace("Rp","").replace(".",""))
			total_seller_discount = total_seller_discount + self.seller_voucher or 0.0

		if total_seller_discount:
			self.apply_discount_on = "Grand Total"
			self.discount_amount = flt(total_seller_discount) or 0.0
			seller_discount_per_item = total_seller_discount / (len(self.items) or 1)

def update_seller_notes(self):
	if not frappe.get_meta("Marketplace CSO"):
		return

	if frappe.get_list("Marketplace CSO",{"name":self.no_online_order.strip(), "status":("not in", ["Completed","Cancelled"]),"sales_invoice":""}):
		cso = frappe.get_doc("Marketplace CSO", self.no_online_order.strip())
		if cso:
			if cso.seller_notes:
				self.seller_notes = cso.seller_notes


def si_validate(self, method):
	is_online_shop=0;
	if "is_online_shop" in frappe.db.get_table_columns("Company"):
		is_online_shop = frappe.db.get_value("Company", self.company, "is_online_shop")

	if not is_online_shop: return

	if not self.no_online_order: #skip if not-online_order
		self.order_status = ""
		return 

	apply_marketplace_workflow = 0
	if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
		apply_marketplace_workflow = frappe.get_value("Company", self.company,"apply_marketplace_workflow") or 0

	meta = frappe.get_meta(self.doctype)
	if meta.has_field("no_online_order"):
		if self.no_online_order:
			self.posting_date = nowdate()
			self.posting_time = nowtime()
			invoice_no = frappe.db.sql('''select name from `tabSales Invoice` where docstatus=1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)
	
			if invoice_no and self.no_online_order and len(cstr(self.no_online_order)) > 10 and not self.is_return:
				frappe.throw(_("Same Invoice No: {0} found").format(self.no_online_order))

			'''Generate random AWB NO if not specified for barcode purpose'''
			if not self.awb_no and "generate_awb_barcode" in frappe.db.get_table_columns("Company") and not self.is_return:
				if frappe.db.get_value("Company", {"name":self.company}, "generate_awb_barcode"):
					temp = frappe.generate_hash()[:12].upper()
					self.awb_no = temp #+ "-" + self.no_online_order[-5:]

			calculate_mp_seller_discount(self)


	if meta.has_field("awb_no") and meta.has_field("order_status"):
		if self.is_return: 
			self.order_status = ""

		else: calculate_shipping_internal_charges(self, self.base_total)

	meta = frappe.get_meta("Sales Invoice Item")

	if meta.has_field("marketplace_return") and self.is_return:
		if apply_marketplace_workflow:
			for d in self.items:
				if not d.marketplace_return:
					frappe.throw(_("Row {0}.Sales Return must be created from Marketplace Return".format(d.idx)))

				elif [mr for mr in frappe.get_list("Marketplace Return Item", fields="parent", filters = [["parent","=",d.marketplace_return], ["sales_invoice","=",d.item_invoice], ["item_code","=",d.item_code], ["name","=",d.ref_item_name], ["qty","!=",abs(d.qty)]]) if mr]:
					frappe.throw(_("Row {0}. Qty is different from Marketplace Return Qty: {1}".format(d.idx, d.marketplace_return)))

def si_before_submit(self, method):
	if "no_online_order" in frappe.db.get_table_columns(self.doctype) and "is_online_shop" in frappe.db.get_table_columns("Company"):
		if self.no_online_order:
			self.posting_date = nowdate()
			self.posting_time = nowtime()
			#frappe.msgprint(self.posting_date)
			if "delivery_date" in frappe.db.get_table_columns(self.doctype):
				self.delivery_date = nowdate()

	if "max_discount_amount" in frappe.db.get_table_columns("Customer") and not self.is_return:
		max_discount_amount = flt(frappe.db.get_value("Customer", {"name":self.customer}, "max_discount_amount"))
		if max_discount_amount != 0.0 and flt(self.discount_amount) > max_discount_amount:
			self.discount_amount = max_discount_amount
			self.additional_discount_percentage = 0

	#controller to set order_status
	meta = frappe.get_meta(self.doctype)
	if meta.has_field("awb_no") and meta.has_field("order_status") :
		if not self.no_online_order:return #skip if not-online_order

		from custom1.marketplace_flow.marketplace_flow import validate_mandatory
		msg = validate_mandatory(self)
		if msg: frappe.throw(msg)

		apply_marketplace_workflow = 0
		if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
			apply_marketplace_workflow = frappe.get_value("Company", self.company,"apply_marketplace_workflow") or 0

		if (not apply_marketplace_workflow or (self.order_status == "To Pack" and self.packing_start and self.packing_end)) and not self.is_return:
			self.delivery_date = nowdate()
			self.posting_date = nowdate()
			self.picked_and_packed = 1
			self.order_status = "Completed"
		elif self.is_return: self.order_status = ""
		elif apply_marketplace_workflow and not self.packing_end:
			frappe.throw("Order status must be = To Pack and done Pack start-Pack end. {0} has invalid order status: {1}".format(self.name, self.order_status))


def si_before_cancel(self, method):
	#controller to set order_status to cancelled if document is cancelled

	meta = frappe.get_meta(self.doctype)
	if meta.has_field("awb_no") and meta.has_field("order_status"):
		self.order_status = "Cancelled"
		self.picked_and_packed = 0
		self.delivery_date = ""


def validate_selling_price(it):
	last_purchase_rate, is_stock_item = frappe.db.get_value("Item", it.item_code, ["last_purchase_rate", "is_stock_item"])
	last_purchase_rate_in_sales_uom = last_purchase_rate / (it.conversion_factor or 1)
	
	#if flt(it.rate) < flt(flt(last_purchase_rate_in_sales_uom) * 0.97):
	#	frappe.throw("Selling rate {0} is below its last purchase rate: {1}".format(cstr(it.rate), it.item_code))

	last_valuation_rate = frappe.db.sql("""
				SELECT valuation_rate FROM `tabStock Ledger Entry` WHERE item_code = %s
				AND warehouse = %s AND valuation_rate > 0
				ORDER BY posting_date DESC, posting_time DESC, name DESC LIMIT 1
				""", (it.item_code, it.warehouse))
	if last_valuation_rate:
		last_valuation_rate_in_sales_uom = last_valuation_rate[0][0] / (it.conversion_factor or 1)
		if is_stock_item and flt(it.rate) < flt(flt(last_valuation_rate_in_sales_uom)):
			frappe.throw("Selling rate {0} is below its valuation rate: {1}".format(cstr(it.rate), it.item_code))

@frappe.whitelist()
def make_purchase_order_for_drop_shipment(source_name, target_doc=None, for_supplier=None):
	def set_missing_values(source, target):
		if for_supplier:
			target.supplier = for_supplier
		target.apply_discount_on = ""
		target.additional_discount_percentage = 0.0
		target.discount_amount = 0.0

		if for_supplier:
			default_price_list = frappe.get_value("Supplier", for_supplier, "default_price_list")
			if default_price_list:
				target.buying_price_list = default_price_list

		if any( item.delivered_by_supplier==1 for item in source.items):
			if source.shipping_address_name:
				target.shipping_address = source.shipping_address_name
				target.shipping_address_display = source.shipping_address
			else:
				target.shipping_address = source.customer_address
				target.shipping_address_display = source.address_display

			target.customer_contact_person = source.contact_person
			target.customer_contact_display = source.contact_display
			target.customer_contact_mobile = source.contact_mobile
			target.customer_contact_email = source.contact_email

		else:
			target.customer = ""
			target.customer_name = ""

		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
		target.schedule_date = source.delivery_date
		target.qty = flt(source.qty) - flt(source.ordered_qty)
		target.stock_qty = (flt(source.qty) - flt(source.ordered_qty)) * flt(source.conversion_factor)

	doclist = get_mapped_doc("Sales Order", source_name, {
		"Sales Order": {
			"doctype": "Purchase Order",
			"field_no_map": [
				"address_display",
				"contact_display",
				"contact_mobile",
				"contact_email",
				"contact_person",
				"taxes_and_charges",
				"notes"
			],
			"validation": {
				"docstatus": ["=", 1]
			}
		},
		"Sales Order Item": {
			"doctype": "Purchase Order Item",
			"field_map":  [
				["name", "sales_order_item"],
				["parent", "sales_order"],
				["stock_uom", "stock_uom"],
				["uom", "uom"],
				["conversion_factor", "conversion_factor"],
				["delivery_date", "schedule_date"]
			],
			"field_no_map": [
				"rate",
				"price_list_rate"
			],
			"postprocess": update_item,
			"condition": lambda doc: doc.ordered_qty < doc.qty #and doc.supplier == for_supplier
		}
	}, target_doc, set_missing_values)

	return doclist

@frappe.whitelist()
def submit_awb_invoice(ref_no):
	inv = frappe.get_doc("Sales Invoice",ref_no) #frappe.db.get_value("Sales Invoice", {"awb_no":ref_no, "is_return":0, "docstatus":0}, "name") or frappe.db.get_value("Sales Invoice", {"name":ref_no, "is_return":0, "docstatus":0}, "name"))
	#frappe.msgprint(inv.name)
	if inv:
		inv.flags.ignore_permissions = True
		inv.delivery_date = nowdate()
		inv.posting_date = nowdate()
		inv.posting_time = nowtime()

		inv.picked_and_packed = 1
		#inv.title = "[PnP]" + inv.title
		inv.submit()
		frappe.db.commit()
		return

def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start

def submit_after_save(self, method):
	if "phase" in frappe.db.get_table_columns(self.doctype) and "awb_no" in frappe.db.get_table_columns(self.doctype):
		#self.submit()
		#frappe.db.commit()
		return

@frappe.whitelist()
def create_ste_delivery(ref_no):
	doc = {}
	prev = {}
	awb_no = ""
	item_code = ""
	design = ""
	message = []
	p = []

	if ref_no.find("-") >= 0 and find_nth(ref_no,"-",2) > 0:
		a = ref_no.split("-",2)
		awb_no = a[0]
		item_code = a[1]
		design = a[2]
	else:
		awb_no = ref_no
		
	if not item_code:
		p = frappe.db.sql('''select name from `tabStock Entry` where awb_no=%s and docstatus=1 and ifnull(phase,'')<>'' 
				order by creation desc limit 1''', awb_no, as_dict=0)
	else:
		p = frappe.db.sql('''select st.name from `tabStock Entry` st join `tabStock Entry Detail` it on it.parent=st.name 
				where st.awb_no=%s and st.docstatus=1 and ifnull(st.phase,'')<>'' and it.item_code=%s 
				order by st.creation desc limit 1''', (awb_no,item_code), as_dict=0)

	#prev = frappe.get_doc("Stock Entry", {"awb_no":ref_no, "phase":"Pickup", "docstatus":1}) 
	if p:
		prev = frappe.get_doc("Stock Entry", cstr(p[0][0])) 
	else:
		message.append("Error")
		message.append("AWB No: {0}. Please check previous entry has been made".format(awb_no))
		return message

	#if frappe.db.get_value("Stock Entry", {"awb_no":ref_no, "phase":"Delivery", "docstatus":1}, "name"):
	if prev.phase == "Delivery":
		message.append("Error")
		message.append("AWB No: {0}. Status is delivered".format(awb_no))
		return message

	if prev:
		doc = frappe.new_doc("Stock Entry")
		doc.posting_date = nowdate()
		doc.posting_time = nowtime()

		if prev.phase == "Items Collected":
			doc.purpose = "Material Transfer"
			doc.phase = "Printed"
			doc.awb_no = prev.awb_no
			doc.from_warehouse = "Printing - YJ"
			doc.to_warehouse = "QC - YJ"

			if not prev.is_job:			
				doc.purpose = "Material Issue"
				doc.phase = "Delivery"
				doc.awb_no = prev.awb_no
				doc.from_warehouse = "Packing - YJ"
				doc.to_warehouse = ""

		elif prev.phase == "New Order":
			#message.append("Error")
			#message.append("AWB No: {0} has not passed Items Collection QC".format(awb_no))
			#return message
			doc.purpose = "Material Issue"
			doc.phase = "Delivery"
			doc.awb_no = prev.awb_no
			doc.from_warehouse = "Packing - YJ"
			doc.to_warehouse = ""

		elif prev.phase == "Printed":
			message.append("Error")
			message.append("AWB No: {0} has not passed QC yet".format(awb_no))
			return message
		elif prev.phase == "QC":
			doc.purpose = "Material Issue"
			doc.phase = "Delivery"
			doc.awb_no = prev.awb_no
			doc.from_warehouse = "Packing - YJ"
			doc.to_warehouse = ""
		else:
			message.append("Error")
			message.append("Invalid AWB {0}. Previous Status: {1}".format(awb_no,prev.phase))


		doc.title = doc.phase +"-"+ doc.purpose

		if prev.phase == "QC" or doc.phase == "Delivery" or doc.phase == "New Order":
			for d in prev.items:
				doc.append("items",{
						"item_code": d.item_code,
						"item_name": d.item_name,	
						"s_warehouse": doc.from_warehouse,
						"t_warehouse": doc.to_warehouse,
						"qty": d.qty,
						"basic_rate":d.basic_rate,
						"basic_amount":d.basic_amount,
						"design": d.design
				})
		else:
			doc.append("items",{
						"item_code": item_code,
						#"item_name": d.item_name,	
						"s_warehouse": doc.from_warehouse,
						"t_warehouse": doc.to_warehouse,
						"qty": 1,
						#"basic_rate":d.basic_rate,
						#"basic_amount":d.basic_amount,
						"design": design
				})

		doc.flags.ignore_permissions = True
		doc.insert()
		doc.submit()
		frappe.db.commit()

		message.append("Success")
		message.append(doc.name)
		return message
	else:
		message.append("Error")
		message.append("AWB {0} is not yet ready for pickup".format(awb_no))
		return message

@frappe.whitelist()
def populate_prev_items(ref_no):
	prev = []
	new_order = {}
	awb_no = ""
	item_code = ""
	design = ""
	message = []
	msg_error = []

	total_order = 0
	total_printed = 0

	if ref_no.find("-") >= 0 and find_nth(ref_no,"-",2) > 0:
		a = ref_no.split("-",2)
		awb_no = a[0]
		item_code = a[1]
		design = a[2]
	else:
		awb_no = ref_no
		
	new_order = frappe.get_doc("Stock Entry", {"awb_no":ref_no, "phase":"New Order", "docstatus":1}) 
	#prev = frappe.get_doc("Stock Entry", {"awb_no":ref_no, "phase":"Printing", "docstatus":1}) 

	#prev = frappe.db.sql('''select sum(qty) as qty from `tabStock Entry` st join `tabStock Entry Detail` it on it.parent=st.name 
	#			where st.awb_no=%s and st.docstatus=1 and ifnull(st.phase,'')='Printing'
	#			order by st.creation desc limit 1''', awb_no, as_dict=0)
	
	if not new_order:
		message.append("Error")
		message.append("AWB No: {0} Not Found in Order Data".format(awb_no))
		return message


	#if new_order:
	#	for d in new_order.items:
	#		total_order += d.qty

	if new_order:
		for d in new_order.items:
			#total_printed += d.qty

			message.append({
						"item_code": d.item_code,
						"item_name": d.item_name,	
						"s_warehouse": d.s_warehouse,
						"t_warehouse": d.t_warehouse,
						"qty": d.qty,
						"conversion_factor": d.conversion_factor,
						"basic_rate":d.basic_rate,
						"basic_amount":d.basic_amount,
						"design": d.design
					})

		#if total_order != total_printed:
		#	msg_error.append("Error")
		#	msg_error.append("Qty difference is found between Order:{0} and Printed:{1} for AWB No: {2}".format(cstr(total_order),cstr(total_printed),awb_no))
		#	return msg_error
		#else:
		return message

def si_before_insert(self, method):
	if self.company: #make sure only import online_order
		return
	#company = frappe.db.get_value("Global Defaults", None, "default_company") 
	company = frappe.db.get_single_value('Global Defaults', 'default_company')

	apply_marketplace_workflow = 0

	if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
		apply_marketplace_workflow = frappe.get_value("Company", self.company,"apply_marketplace_workflow") or 0

	is_online_shop=0;
	if "is_online_shop" in frappe.db.get_table_columns("Company"):
		is_online_shop = frappe.db.get_value("Company", company, "is_online_shop")

	if not is_online_shop and company not in ("PARAGON JAYA","SILVER PHONE", "AN Electronic", "TOKO BELAKANG", "NEXTECH","PT. TRIGUNA JAYA SENTOSA", "HANIPET KOTEGA","BOMBER STORE","HIHI STORE","CENTRA ONLINE"):
		return

	same_invoice = ""
	cost_center = ""

	# make sure no double order_no
	if self.naming_series and len(cstr(self.naming_series)) >= 10:
		no_online_order = self.naming_series.strip()
		self.no_online_order = cstr(no_online_order)

		if (self.is_return):
			self.name = "R-" + self.no_online_order
		else:
			self.name = cstr(self.no_online_order)

		same_invoice = frappe.db.sql('''select no_online_order from `tabSales Invoice` where docstatus <= 1 and is_return != 1 and no_online_order=%s limit 1''', self.no_online_order.strip(), as_dict=0)
		if self.no_online_order and same_invoice:
			frappe.throw(_("Same Invoice No exists : {0}").format(self.no_online_order))

	#make sure only import order yg sudah diproses
	status_order = ["HARUS DIKIRIM","MENUNGGU DIPICKUP","SIAP DIKIRIM","AKAN DIKIRIM","SUDAH DIPROSES","PERLU DIKIRIM","SEDANG DIPROSES","READY TO SHIP","READY_TO_SHIP","DIPROSES PELAPAK"]

	#update order_Status
	if "order_status" in frappe.db.get_table_columns(self.doctype):
		order_status = self.order_status
		self.order_status = ""

		if order_status:
			if order_status.upper() in status_order or "SEDANG DIPROSES" in order_status.upper() or "SUDAH DIPROSES" in order_status.upper() or "DIPROSES PELAPAK" in order_status.upper():
				#frappe.throw(_("Order Belum Diproses / Batal / Terkirim / Selesai: {0}").format(cstr(self.no_online_order)))
				#if not apply_marketplace_workflow: #"finnix" in get_site_name("finnix.vef-solution.com"):
				#	self.order_status = "Pending"
				#else: 
				self.order_status = "To Pick"

				self.pending_remarks = order_status
			else: 
				self.order_status = "Pending"
				self.pending_remarks = order_status
				status_order = ["BELUM BAYAR","PENDING","UNPAID","MENUNGGU PEMBAYARAN"]
				for c in status_order:
					if c in order_status.upper():
						self.order_status = "Pending"
						self.pending_remarks = "Belum Dibayar / Pembayaran Belum Terverifikasi"
						break

				status_order = ["BATAL","CANCEL"]
				for c in status_order:
					if c in order_status.upper():
						self.order_status = "Cancelled"
						self.pending_remarks = "Status order dibatalkan"
						break


	#set marketplace_courier
	if "marketplace_courier" in frappe.db.get_table_columns(self.doctype):
		ignore_courier_master_check = frappe.db.get_single_value("Local Marketplace Settings","ignore_courier_master_check") or 0
 
		courier = frappe.db.sql('''select name from `tabMarketplace Courier` where (name like %s or courier_name like %s or description like %s) limit 1''', 
			(("%" + self.courier.strip() + "%"),("%" + self.courier.strip() + "%"),("%" + self.courier.strip() + "%")), as_dict=0)

		if courier: 
			values = frappe.db.get_value("Marketplace Courier", courier[0][0], ["letter_head","courier_type"])
			if values:
				if frappe.db.get_value("Letter Head", values[0], "name"):
					self.letter_head = values[0] or ""

			self.marketplace_courier = courier[0][0]
			self.courier_type = values[1] or ""
		elif not ignore_courier_master_check:
			frappe.throw(_("Marketplace Courier master not found using keyword '{0}'. Order No: {1}").format(self.courier, cstr(no_online_order)))


	self.status = "Draft"
	self.update_stock = 1
	self.company = company

	if not cstr(getdate(cstr(self.posting_date))):
		frappe.throw(_("Invalid date format: {0}").format(cstr(self.posting_date)))
	else:
		if "order_date" in frappe.db.get_table_columns(self.doctype):
			self.order_date = cstr(getdate(cstr(self.posting_date))) #self.posting_date

		self.posting_time = nowtime() or get_time("23:59:00") #datetime.datetime.strptime("23:59:59", "%H:%M:%S")
		self.posting_date = nowdate() #cstr(getdate(cstr(self.posting_date))) #cstr(getdate(cstr(self.posting_date)))
		self.import_time = now_datetime()

		''' insert marketplace scorecard '''
		if not frappe.db.exists("Marketplace Fulfillment Score Card",{"transaction_ref_no":self.name, "type":"Fulfillment Admin"}):
			scorecard = frappe.new_doc("Marketplace Fulfillment Score Card")
			scorecard.type = "Fulfillment Admin"
			scorecard.transaction_ref_no = self.name
			scorecard.time_start = self.order_date
			scorecard.time_end = now_datetime()

			hour_diff = time_diff_in_hours(scorecard.time_end, scorecard.time_start)
			score_list = frappe.get_list("Score Card Template",fields=["name"],filters=[["time_factor",">=",hour_diff],["score_type","=","Fulfillment Admin"]],order_by="time_factor")
			if score_list:
				scorecard.score = score_list[0].name

			scorecard.save()


	if not frappe.db.get_value("Customer", self.customer, "name"):
		frappe.throw(_("Customer {0} not found").format(self.customer))

	if not self.selling_price_list:
		self.selling_price_list = frappe.db.get_value("Customer", {"name":self.customer}, "default_price_list") #"Price 1"
		if not self.selling_price_list:
			self.selling_price_list = frappe.db.get_single_value('Selling Settings', 'selling_price_list')	

	self.due_date = add_days(self.posting_date, 14);

	if self.no_online_order and len(cstr(self.no_online_order)) >= 10:
		if (self.is_return):
			self.naming_series = "R/.no_online_order.-.##"
		else:
			self.naming_series = "no_online_order.-.##"


		#frappe.throw(_("naming_series is {0} , name is {1}").format(self.naming_series,self.name))

		if "is_official_store" in frappe.db.get_table_columns("Customer"):
			is_official_store = frappe.db.get_value("Customer", {"name":self.customer}, "is_official_store") or "0"

		self.territory = frappe.db.get_value("User Permission", {"user":frappe.session.user, "allow":"Territory"}, "for_value") or \
					frappe.db.get_value("Customer", {"name":self.customer}, "territory") or ""

		calculate_mp_seller_discount(self)
		update_seller_notes(self)

		base_total = 0.0
		for d in self.items:
			if not d.item_code:
				frappe.throw(_("Item Code / SKU is required : {0}").format(self.no_online_order))
			
			#item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and item_code=%s limit 1''', (d.item_code.strip()), as_dict=0) or \
			#	frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
			#	((%s like concat (%s,item_code,%s)) or item_name like %s or description like %s) limit 1''', 
			#	(d.item_code.strip(),"%",("%" + d.item_code.strip() + "%"),("%" + d.item_code.strip() + "%")), as_dict=0)
			
			item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and item_code=%s limit 1''', (d.item_code.strip()), as_dict=0) or \
				frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
				(item_name like %s or description like %s) limit 1''', 
				(("%" + d.item_code.strip() + "%"),("%" + d.item_code.strip() + "%")), as_dict=0)

			#if not item_code:
			#	item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
			#			(%s like concat (%s,item_code,%s)) limit 1''', (d.item_code.strip(),"%","%"), as_dict=0)

			if item_code:
				d.item_code = cstr(item_code[0][0])
				d.item_name = frappe.db.get_value("Item", {"name":d.item_code}, "item_name") or d.item_code
				if not d.description:
					d.description = d.item_name

				if not d.rate:
					from erpnext.stock.utils import get_incoming_rate
					d.rate = get_incoming_rate(args={"item_code":d.item_code}) or 10000.0
					if not d.rate:
						frappe.throw(_("Harga kosong untuk item : {0}, Order ID: {1}").format(d.item_code,self.no_online_order))

				from erpnext.stock.utils import get_stock_balance

				warehouse = frappe.db.get_value("User Permission", {"user":frappe.session.user, "allow":"Warehouse"}, "for_value") or \
						frappe.db.get_single_value('Stock Settings', 'default_warehouse') or ""

				is_stock_item = frappe.db.get_value("Item", {"name":d.item_code}, "is_stock_item")
				if warehouse:
					d.warehouse = warehouse
				if warehouse and is_stock_item and not frappe.db.get_single_value('Stock Settings', 'allow_negative_stock'):
					stock_balance = get_stock_balance(d.item_code, d.warehouse, self.posting_date or nowdate(), self.posting_time)
					#if d.item_code == "A309PN":
					#	frappe.throw(_("Item : {0} Stock: {1} required: {2} Posting Date: {3} Posting Time: {4} Order time: {5}").format(d.item_code, cstr(stock_balance),cstr(d.qty), cstr(self.posting_date), cstr(self.posting_time), cstr(get_time(self.posting_date))))
					if (stock_balance - flt(d.qty)) < 0.0:
						ignore_insufficient_stock = frappe.db.get_single_value("Local Marketplace Settings","ignore_insufficient_stock") or 0
						if not ignore_insufficient_stock:
							frappe.throw(_("Insufficient Stock {0} > {1} for item : {2} in Warehouse {3}").format(cstr(d.qty),cstr(stock_balance),d.item_code,d.warehouse))
						elif ignore_insufficient_stock: 
							self.insufficient_stock = ignore_insufficient_stock

				elif is_stock_item and not warehouse:
					frappe.throw(_("Warehouse not found for item : {0}").format(d.item_code))
			else:
				frappe.throw(_("Item Code / SKU not found : {0}, Order: {1}").format(d.item_code, self.no_online_order))

			if not d.qty:
				frappe.throw(_("Qty tidak ada untuk Item : {0}").format(d.item_code))

			cost_center=frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value")
			if cost_center:
				d.cost_center = cost_center 
			else:
				d.cost_center = frappe.db.get_value("Company", company, "cost_center") 

			#remove currency symbol if any convert to float
			_rate = 0.0
			_disc = 0.0
			if not flt(cstr(d.rate)):
				_rate = flt(cstr(d.rate or "0").replace("Rp","").replace(".","")) #cstr(Decimal(sub(r'[^\d.]', '', cstr(d.rate or "0"))))

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
			item_group = frappe.db.get_value("Item", {"name":d.item_code}, "item_group") or "Products"

			if item_group and frappe.db.table_exists("Marketplace Fees"):
				mp_fee = frappe.db.get_value("Marketplace Fees", {"parent":item_group, "marketplace_store_name": self.customer}, ["marketplace_fee_percentage","max_fee_amount"])
				if not mp_fee:
					mp_fee = frappe.db.get_value("Marketplace Fees", {"parent":"Products", "marketplace_store_name": self.customer}, ["marketplace_fee_percentage","max_fee_amount"])
				if mp_fee:
					d.discount_percentage = mp_fee[0] or 0.0
				if flt(d.discount_percentage) != 0.0:
					if ((flt(d.discount_percentage)/100.0 * flt(d.price_list_rate)) > mp_fee[1]) and mp_fee[1] > 0:
						d.rate = flt(d.price_list_rate) - flt(mp_fee[1])
					else:
						d.rate = flt(d.price_list_rate) * (100.0 - d.discount_percentage)/100.0
					d.amount = flt(d.price_list_rate) * flt(d.qty)

			if "total_qty" in frappe.db.get_table_columns(self.doctype):
				self.total_qty = flt(self.total_qty) + flt(d.qty)

			#if "lazada_sku" in frappe.db.get_table_columns(d.doctype):
			#	self.shipping_fee = flt(self.shipping_fee) + flt(d.shipping_fee)

			base_total = base_total + flt(d.rate) * flt(d.qty)
	else:
		frappe.throw(_("Online Order No : {0} is invalid").format(self.no_online_order or ""))

	'''Generate random AWB NO if not specified for barcode purpose'''
	if not self.awb_no and "generate_awb_barcode" in frappe.db.get_table_columns("Company") and not self.is_return:
		if frappe.db.get_value("Company", {"name":self.company}, "generate_awb_barcode"):
			temp = frappe.generate_hash()[:12].upper()
			self.awb_no = temp #+ "-" + self.no_online_order[-5:]


	#set courier_type
	if "courier_type" in frappe.db.get_table_columns(self.doctype):
		if "GRAB" in self.courier.upper() or "GOJEK" in self.courier.upper() or "GO-JEK" in self.courier.upper():
			self.courier_type = "Same Day"
		else: self.courier_type = "Regular"

	#set package_weight
	if "package_weight" in frappe.db.get_table_columns(self.doctype):
		if self.package_weight:
			if "GR" in self.package_weight.upper():
				self.package_weight = flt(cstr(self.package_weight).split(" ")[0],3)/1000.0 #convert to kg
			elif "KG" in self.package_weight.upper():
				self.package_weight = flt(cstr(self.package_weight).split(" ")[0],3) #Kg
			else: 
				frappe.throw(_("Error Weight format for Order No : {0}").format(self.no_online_order or ""))
	
	#frappe.throw(_("Shipping Fee : {0}").format(self.shipping_fee))
	if self.shipping_fee:
		#shipping_fee = 0.0 
		if not flt(cstr(self.shipping_fee)):
			shipping_fee = flt(cstr(self.shipping_fee or "0").replace("Rp","").replace(".","")) #cstr(Decimal(sub(r'[^\d.]', '', cstr(self.shipping_fee or "0"))))
			self.shipping_fee = shipping_fee #cstr(shipping_fee).replace(".","")

		insurance_fee = 0.0 
		if not flt(cstr(self.insurance_fee)):
			insurance_fee = flt(cstr(self.insurance_fee or "0").replace("Rp","").replace(".","")) #cstr(Decimal(sub(r'[^\d.]', '', cstr(self.insurance_fee or "0"))))
			self.insurance_fee = insurance_fee #cstr(insurance_fee).replace(".","")

		
		account_insurance = ""
		#frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Insurance Fee%' limit 1''', as_dict=0) or \
		#			frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Asuransi%' limit 1''', as_dict=0)

		if self.insurance_fee and account_insurance:
			self.append("taxes", {
				"charge_type": "Actual",
				"account_head": cstr(account_insurance[0][0] if account_insurance else account_head[0][0]),
				"cost_center": frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value") or frappe.db.get_value("Company", company, "cost_center"),
				"description": "Insurance Fee",
				"tax_amount": flt(self.insurance_fee)
			})

	calculate_shipping_internal_charges(self, base_total)

def calculate_shipping_internal_charges(self, base_total=0):
	''' Calculate custom insurance fee '''
	if self.is_return: return

	if "apply_marketplace_workflow" in frappe.db.get_table_columns("Company"):
		if not frappe.get_value("Company", self.company,"apply_marketplace_workflow"): return

	if self.marketplace_courier:
		if not base_total: base_total = self.base_total
		if not base_total: return

		self.internal_charges = []
		doc = frappe.get_doc("Marketplace Courier", self.marketplace_courier)
		apply_charges = False

		#frappe.throw("item total={0}".format(cstr(self.total)))
		if doc:
			multiply_factor = doc.multiply_factor or 0.0 

			if (flt(base_total) >= flt(doc.min_total_amount)): apply_charges = True
			elif multiply_factor and (flt(self.shipping_fee) * multiply_factor < flt(base_total)): apply_charges = True

			if apply_charges:
				for d in doc.charges:
					if d.exclude_this_customer != self.customer:
						self.append("internal_charges", {
							"charge_type": d.charge_type,
							"account_head": d.account_head,
							"cost_center": d.cost_center or frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value") or frappe.db.get_value("Company", self.company, "cost_center"),
							"description": d.description or d.account_head or "Additional Charge",
							"rate": d.rate,
							"tax_amount": d.tax_amount if d.charge_type == "Actual" else d.rate*base_total/100.0
						})

	if self.marketplace_courier and self.shipping_fee and not self.taxes:
		account_head = ""
		is_shipping = 0
		if self.marketplace_courier:
			doc = frappe.db.get_value("Marketplace Courier", self.marketplace_courier,["shipping_account","post_to_shipping_account"])
			if doc:
				account_head = doc[0] or ""
				is_shipping = doc[1] or 0

		self.taxes = [];
		if not account_head:
			account_head = frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Shipping Fee%' limit 1''', as_dict=0) or \
				frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Freight%' limit 1''', as_dict=0) or \
				frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Ongkos Kirim%' limit 1''', as_dict=0) or \
				frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Ekspedisi%' limit 1''', as_dict=0) or \
				frappe.db.sql('''select name from `tabAccount` where is_group=0 and name like '%Kurir%' limit 1''', as_dict=0)
			if account_head: account_head = account_head[0][0]

		if account_head and is_shipping:
			self.append("taxes", {
				"charge_type": "Actual",
				"account_head": cstr(account_head),
				"cost_center": frappe.db.get_value("User Permission", {"name":frappe.session.user, "allow":"Cost Center"}, "for_value") or frappe.db.get_value("Company", self.company, "cost_center"),
				"description": "Shipping Fee (Ongkir)",
				"tax_amount": flt(self.shipping_fee)
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
		where si.docstatus=1 and customer=%s and item_code=%s
		and si.is_return=0 and si_item.rate > 0 order by si.posting_date desc, si.posting_time desc limit 1''', (customer,item_code), as_dict=0)

@frappe.whitelist()
def get_last_rate_by_customer_so(customer,item_code):
	return frappe.db.sql('''select si_item.rate_mtr, si_item.rate from `tabSales Order` si join `tabSales Order Item` si_item on si.name=si_item.parent
		where si.docstatus=1 and customer=%s and item_code=%s
		and si_item.rate > 0 order by si.transaction_date, si.name desc limit 1''', (customer,item_code), as_dict=0)

@frappe.whitelist()
def get_last_rate_by_supplier(supplier,item_code):
	return frappe.db.sql('''select si_item.rate from `tabPurchase Invoice` si join `tabPurchase Invoice Item` si_item on si.name=si_item.parent
		where si.docstatus=1 and supplier=%s and item_code=%s
		and si.is_return=0 and si_item.rate > 0 order by si.posting_date desc, si.posting_time desc limit 1''', (("%" + supplier + "%"),item_code), as_dict=0)

@frappe.whitelist()
def get_last_rate_by_supplier_po(supplier,item_code):
	return frappe.db.sql('''select si_item.rate_mtr, si_item.rate from `tabPurchase Order` si join `tabPurchase Order Item` si_item on si.name=si_item.parent
		where si.docstatus=1 and supplier=%s and item_code=%s
		and si_item.rate > 0 order by si.transaction_date desc, si.name desc limit 1''', (supplier,item_code), as_dict=0)

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

	condition = ""
	# Get positive outstanding sales /purchase invoices/ Fees
	if args.get("voucher_type") and args.get("voucher_no"):
		condition += " and voucher_type='{0}' and voucher_no='{1}'"\
			.format(frappe.db.escape(args["voucher_type"]), frappe.db.escape(args["voucher_no"]))

	condition = condition + " and company='{0}'".format(args.get("company"))

	if args.get("from_date") and args.get("to_date") and not args.get("show_all"):
		outstanding_invoices = get_outstanding_invoices2(args.get("party_type"), args.get("party"),
			args.get("party_account"), condition=condition + " and posting_date between '{0}' and '{1}'".format(args.get("from_date"), args.get("to_date")))
	else:
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
		if args.get("from_date") and args.get("to_date") and not args.get("show_all"):
			orders_to_be_billed =  get_orders_to_be_billed(args.get("posting_date"),args.get("party_type"),
				args.get("party"), party_account_currency, company_currency,condition=condition + " and transaction_date between '{0}' and '{1}'".format(args.get("from_date"), args.get("to_date")))
		else:
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
			posting_date, name limit 20
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
	old_docs = frappe.db.sql ("""SELECT name, creation FROM `tabFile` where datediff(now(),creation) > 0 
		and file_name not like '%into-the-dawn%' and file_name not like '%Generate_Template%' 
		and attached_to_doctype in ('Data Import') order by creation desc""", as_dict=1)

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