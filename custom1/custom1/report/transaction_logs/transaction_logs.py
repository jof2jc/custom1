# Copyright (c) 2013, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	if not filters: filters = {}
	columns = get_columns()
	last_col = len(columns)

	if filters.get("party_type")=="Customer": 
		item_list = get_items_customer(filters) 
	else: 
		item_list = get_items_supplier(filters)
	

	data = []
	for d in item_list:
		row = [d.party_type,
		d.party_name, d.transtype, d.name, d.posting_date, d.item_code, d.item_name,
		d.item_group, d.description,
		d.qty, d.price_list_rate, d.discount_percentage, d.rate]

		
		data.append(row)

	return columns, data

def get_columns():
	return [
                _("Party Type") + "::100",
		_("Party") + ":Dynamic Link/Party Type:100",
                _("Trans Type") + "::120",		
		_("Trans No") + (":Dynamic Link/Trans Type:120"),
                _("Posting Date") + ":Date:100",
		_("Item Code") + ":Link/Item:120", _("Item Name") + "::120",
		_("Item Group") + ":Link/Item Group:100", _("Item Desc") + "::200",		
		_("Qty") + ":Float:60", _("Price List Rate") + ":Currency:120", _("Discount (%)") + ":Float:100",
                _("Net Rate") + ":Currency:120"
	]



def get_conditions1(filters):
	conditions = []

	if filters.get("party_type")=="Customer":
		if filters.get("party"):
			conditions.append("si.customer=%(party)s")
	else:
		if filters.get("party"):
			conditions.append("si.supplier=%(party)s")
		
	if filters.get("company"):
		conditions.append("si.company=%(company)s")

	if filters.get("from_date"):
		conditions.append("si.posting_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("si.posting_date <= %(to_date)s")

	if filters.get("item_code"):
		conditions.append("si_item.item_code=%(item_code)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_conditions2(filters):
	conditions = []

	if filters.get("party_type")=="Customer":
		if filters.get("party"):
                        conditions.append("si.customer=%(party)s")
	else:
		if filters.get("party"):
			conditions.append("si.supplier=%(party)s")
		
	if filters.get("company"):
		conditions.append("si.company=%(company)s")

	if filters.get("from_date"):
		conditions.append("si.transaction_date >= %(from_date)s")
	if filters.get("to_date"):
		conditions.append("si.transaction_date <= %(to_date)s")

	if filters.get("item_code"):
		conditions.append("si_item.item_code=%(item_code)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_items_customer(filters):
	conditions1 = get_conditions1(filters)
	conditions2 = get_conditions2(filters)

	entries1 = frappe.db.sql("""select 'Customer' as party_type,
		si.customer as party_name, 'Sales Invoice' as transtype, si.name, si.posting_date, si_item.item_code, it.item_name,
		it.item_group, it.description,
		si_item.qty, si_item.price_list_rate, si_item.discount_percentage, si_item.rate
		from `tabSales Invoice` si, `tabSales Invoice Item` si_item, `tabItem` it
		where si.name = si_item.parent and si_item.item_code = it.item_code and si.docstatus = 1 %s
		order by si.posting_date desc, si_item.item_code desc""" % conditions1, filters, as_dict=1)
        
	entries2 = frappe.db.sql("""select 'Customer' as party_type,
		si.customer as party_name, 'Delivery Note' as transtype, si.name, si.posting_date, si_item.item_code, it.item_name,
		it.item_group, it.description,
		si_item.qty, si_item.price_list_rate, si_item.discount_percentage, si_item.rate
		from `tabDelivery Note` si, `tabDelivery Note Item` si_item, `tabItem` it
		where si.name = si_item.parent and si_item.item_code = it.item_code and si.docstatus = 1 %s
		order by si.posting_date desc, si_item.item_code desc""" % conditions1, filters, as_dict=1)

	entries3 = frappe.db.sql("""select 'Customer' as party_type,
		si.customer as party_name, 'Sales Order' as transtype, si.name, si.transaction_date as posting_date, si_item.item_code, it.item_name,
		it.item_group, it.description,
		si_item.qty, si_item.price_list_rate, si_item.discount_percentage, si_item.rate
		from `tabSales Order` si, `tabSales Order Item` si_item, `tabItem` it
		where si.name = si_item.parent and si_item.item_code = it.item_code and si.docstatus = 1 %s
		order by si.transaction_date desc, si_item.item_code desc""" % conditions2, filters, as_dict=1)

	return entries1+entries2+entries3

def get_items_supplier(filters):
	conditions1 = get_conditions1(filters)
	conditions2 = get_conditions2(filters)

	entries1 = frappe.db.sql("""select 'Supplier' as party_type,
		si.supplier as party_name, 'Purchase Invoice' as transtype, si.name, si.posting_date, si_item.item_code, it.item_name,
		it.item_group, it.description,
		si_item.qty, si_item.price_list_rate, si_item.discount_percentage, si_item.rate
		from `tabPurchase Invoice` si, `tabPurchase Invoice Item` si_item, `tabItem` it
		where si.name = si_item.parent and si_item.item_code = it.item_code and si.docstatus = 1 %s
		order by si.posting_date desc, si_item.item_code desc""" % conditions1, filters, as_dict=1)
        
	entries2 = frappe.db.sql("""select 'Supplier' as party_type,
		si.supplier as party_name, 'Purchase Receipt' as transtype, si.name, si.posting_date, si_item.item_code, it.item_name,
		it.item_group, it.description,
		si_item.qty, si_item.price_list_rate, si_item.discount_percentage, si_item.rate
		from `tabPurchase Receipt` si, `tabPurchase Receipt Item` si_item, `tabItem` it
		where si.name = si_item.parent and si_item.item_code = it.item_code and si.docstatus = 1 %s
		order by si.posting_date desc, si_item.item_code desc""" % conditions1, filters, as_dict=1)
	
	entries3 = frappe.db.sql("""select 'Supplier' as party_type,
		si.supplier as party_name, 'Purchase Order' as transtype, si.name, si.transaction_date as posting_date, si_item.item_code, it.item_name,
		it.item_group, it.description,
		si_item.qty, si_item.price_list_rate, si_item.discount_percentage, si_item.rate
		from `tabPurchase Order` si, `tabPurchase Order Item` si_item, `tabItem` it
		where si.name = si_item.parent and si_item.item_code = it.item_code and si.docstatus = 1 %s
		order by si.transaction_date desc, si_item.item_code desc""" % conditions2, filters, as_dict=1)

	return entries1+entries2+entries3