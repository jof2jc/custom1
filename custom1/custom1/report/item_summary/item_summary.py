# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)
	item_map = get_item_details()
	pl = get_price_list()
	#last_purchase_rate = get_last_purchase_rate()
	#bom_rate = get_item_bom_rate()
	val_rate_map = get_bin_details()

	from erpnext.accounts.utils import get_currency_precision
	precision = get_currency_precision() or 2
	data = []

	if ("Accounts Manager" in frappe.get_roles(frappe.session.user)):
		for item in sorted(item_map):
			data.append([item.name, item["item_name"], item.actual_qty, item.stock_uom, item.warehouse, 
				pl.get(item.name, {}).get("Selling"), item.valuation_rate, #val_rate_map[item]["val_rate"], #flt(val_rate_map.get(item, 0), precision),
				get_last_purchase_rate(item.name) or 0.0, #flt(last_purchase_rate.get(item.name, 0), precision), 
				item.item_group, item.description			
				#pl.get(item, {}).get("Buying"),
				#flt(bom_rate.get(item, 0), precision)
			])
	else:
		for item in sorted(item_map):
			data.append([item.name, item["item_name"], item.actual_qty, item.stock_uom, item.warehouse, 
				pl.get(item.name, {}).get("Selling"), #item.valuation_rate, #val_rate_map[item]["val_rate"], #flt(val_rate_map.get(item, 0), precision),
				#flt(last_purchase_rate.get(item.name, 0), precision), 
				item.item_group, item.description			
				#pl.get(item, {}).get("Buying"),
				#flt(bom_rate.get(item, 0), precision)
			])

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	if ("Accounts Manager" in frappe.get_roles(frappe.session.user)):
		columns = [_("Item") + ":Link/Item:75", _("Item Name") + "::200", _("Actual Qty") + ":Float:75",  _("UOM") + ":Link/UOM:80", 
			_("Warehouse") + ":Link/Warehouse:125",
			_("Sales Price List") + "::180",
			_("Valuation Rate") + ":Currency:80", _("Last Purchase Rate") + ":Currency:90",
			_("Item Group") + ":Link/Item Group:125", _("Description") + "::150"] 	
			#_("Purchase Price List") + "::180", _("BOM Rate") + ":Currency:90"]
	else:
		columns = [_("Item") + ":Link/Item:75", _("Item Name") + "::200", _("Actual Qty") + ":Float:75",  _("UOM") + ":Link/UOM:80", 
			_("Warehouse") + ":Link/Warehouse:125",
			_("Sales Price List") + "::180",
			#_("Valuation Rate") + ":Currency:80", _("Last Purchase Rate") + ":Currency:90",
			_("Item Group") + ":Link/Item Group:125", _("Description") + "::150"] 	
			#_("Purchase Price List") + "::180", _("BOM Rate") + ":Currency:90"]

	return columns

def get_item_details():
	"""returns all items details"""

	#item_map = {}

	item_map = frappe.db.sql("select it.name, it.item_group, it.item_name, it.description, bin.actual_qty, bin.warehouse, \
		it.stock_uom, bin.valuation_rate from tabItem it left join tabBin bin on (it.name=bin.item_code and it.stock_uom = bin.stock_uom) \
		where it.disabled <> 1 order by it.item_code, it.item_group", as_dict=1)
	#print item_map

	return item_map

def get_price_list():
	"""Get selling & buying price list of every item"""

	rate = {}

	price_list = frappe.db.sql("""select ip.item_code, ip.buying, ip.selling,
		concat(ifnull(cu.symbol,ip.currency), " ", round(ip.price_list_rate,2), " - ", ip.price_list) as price
		from `tabItem Price` ip, `tabPrice List` pl, `tabCurrency` cu
		where ip.price_list=pl.name and pl.currency=cu.name and pl.enabled=1""", as_dict=1)

	for j in price_list:
		if j.price:
			rate.setdefault(j.item_code, {}).setdefault("Buying" if j.buying else "Selling", []).append(j.price)
	item_rate_map = {}
	#print rate

	for item in rate:
		for buying_or_selling in rate[item]:
			item_rate_map.setdefault(item, {}).setdefault(buying_or_selling,
				", ".join(rate[item].get(buying_or_selling, [])))
	#print item_rate_map
	return item_rate_map

def get_last_purchase_rate(item_code):

	item_last_purchase_rate_map = {}

	query = """select * from (select
					result.item_code, result.posting_date,
					result.base_rate
					from (
						(select
							po_item.item_code,
							po_item.item_name,
							po.transaction_date as posting_date,
							po_item.base_price_list_rate,
							po_item.discount_percentage,
							po_item.base_rate
						from `tabPurchase Order` po, `tabPurchase Order Item` po_item
						where po.name = po_item.parent and po.docstatus = 1 and po_item.item_code='{item}')
						union
						(select
							pr_item.item_code,
							pr_item.item_name,
							pr.posting_date,
							pr_item.base_price_list_rate,
							pr_item.discount_percentage,
							pr_item.base_rate
						from `tabPurchase Receipt` pr, `tabPurchase Receipt Item` pr_item
						where pr.name = pr_item.parent and pr.docstatus = 1 and pr_item.item_code='{item}')
						union
						(select
							pi_item.item_code,
							pi_item.item_name,
							pi.posting_date,
							pi_item.base_price_list_rate,
							pi_item.discount_percentage,
							pi_item.base_rate
						from `tabPurchase Invoice` pi, `tabPurchase Invoice Item` pi_item
						where pi.name = pi_item.parent and pi.docstatus = 1 and pi_item.item_code='{item}')
				) result
				order by result.item_code asc, result.posting_date desc) result_wrapper
				group by item_code, posting_date order by posting_date desc""".format( item = item_code )

	#if item_code == 'GC001':
	#	frappe.msgprint(query)

	for idx, d in enumerate (frappe.db.sql(query, as_dict=1)):
		if idx==0:
			item_last_purchase_rate_map.setdefault(d.item_code, d.base_rate)
 
	print item_last_purchase_rate_map

	return item_last_purchase_rate_map.get(item_code,0)

def get_item_bom_rate():
	"""Get BOM rate of an item from BOM"""

	item_bom_map = {}

	for b in frappe.db.sql("""select item, (total_cost/quantity) as bom_rate
		from `tabBOM` where is_active=1 and is_default=1""", as_dict=1):
			item_bom_map.setdefault(b.item, flt(b.bom_rate))

	return item_bom_map

def get_bin_details():
	"""Get bin details from all warehouses"""

	bin_details = frappe.db.sql("""select name, item_code, actual_qty, valuation_rate as val_rate, warehouse
		from `tabBin` order by item_code""", as_dict=1)
	
	#print bin_details

	bin_map = frappe._dict()

	for i in bin_details:
		bin_map.setdefault(i.item_code, i)

	print bin_map
			
	return bin_map

