# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt,cstr

def execute(filters=None):
	if not filters: filters = {}
	item_map = {}
	columns = []
	pl = {}
	columns = get_columns(filters)
	data = []

	#if "SERIMPI" in cstr(frappe.db.get_single_value('Global Defaults', 'default_company')):
	#	if not filters.get("item_code"):
	#		return columns, data #frappe.throw("Please define Item Code")

	item_map = get_item_details(filters)
	
	pl = get_price_list(filters)

	#last_purchase_rate = get_last_purchase_rate()
	#bom_rate = get_item_bom_rate()
	#val_rate_map = get_bin_details()

	from erpnext.accounts.utils import get_currency_precision
	precision = get_currency_precision() or 2

	if "PERDANA DIESEL" or "SERIMPI" in cstr(frappe.db.get_single_value('Global Defaults', 'default_company')):
		for item in sorted(item_map):
			data.append([item.name, item.item_name, item.description, item.actual_qty, item.stock_uom, item.warehouse, item.location_bin, 
				item.avg_qty or 0.0, int(item.actual_qty/item.avg_qty) if item.avg_qty > 0 else 0.0, 
				pl.get(item.name, {}).get("Selling"), item.valuation_rate,
				item.last_purchase_rate or 0.0,
				item.brand, item.item_group
			])	
	elif ("Accounts Manager" in frappe.get_roles(frappe.session.user) or "Accounting" in frappe.get_roles(frappe.session.user)):
		for item in sorted(item_map):
			#avg_sales = get_avg_sales_qty(item.name) or 0.0
			data.append([item.name, item["item_name"], item.actual_qty, item.stock_uom, item.warehouse, item.location_bin,
				#avg_sales, int(item.actual_qty/avg_sales) if avg_sales > 0 else 0.0,
				item.avg_qty or 0.0, int(item.actual_qty/item.avg_qty) if item.avg_qty > 0 else 0.0,
				pl.get(item.name, {}).get("Selling"), item.valuation_rate, #val_rate_map[item]["val_rate"], #flt(val_rate_map.get(item, 0), precision),
				item.last_purchase_rate or 0.0, #get_last_purchase_rate(item.name) or 0.0, #flt(last_purchase_rate.get(item.name, 0), precision), 
				item.brand, item.item_group, item.description			
				#pl.get(item, {}).get("Buying"),
				#flt(bom_rate.get(item, 0), precision)
			])
	else:
		for item in sorted(item_map):
			#avg_sales = get_avg_sales_qty(item.name) or 0.0
			data.append([item.name, item["item_name"], item.actual_qty, item.stock_uom, item.warehouse, item.location_bin,
				#avg_sales, int(item.actual_qty/avg_sales) if avg_sales > 0 else 0.0,
				item.avg_qty or 0.0, int(item.actual_qty/item.avg_qty) if item.avg_qty > 0 else 0.0,
				pl.get(item.name, {}).get("Selling"), #item.valuation_rate, #val_rate_map[item]["val_rate"], #flt(val_rate_map.get(item, 0), precision),
				#flt(last_purchase_rate.get(item.name, 0), precision), 
				item.brand, item.item_group, item.description		
				#pl.get(item, {}).get("Buying"),
				#flt(bom_rate.get(item, 0), precision)
			])

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	if "PERDANA DIESEL" or "SERIMPI" in cstr(frappe.db.get_single_value('Global Defaults', 'default_company')):
		columns = [_("Item") + ":Link/Item:125", _("Item Name") + "::150", _("Description") + "::200", _("Actual Qty") + ":Float:75",  _("UOM") + ":Link/UOM:65", 
			_("Warehouse") + ":Link/Warehouse:125", _("Location") + "::80", _("Sales Avg/30d") + ":Float:100",_("Age Days") + "::70",
			_("Sales Price List") + "::240",
			_("Valuation Rate") + ":Currency:80", _("Last Purchase Rate") + ":Currency:90",
			_("Brand") + ":Link/Brand:100", _("Item Group") + ":Link/Item Group:125"]
	elif ("Accounts Manager" in frappe.get_roles(frappe.session.user) or "Accounting" in frappe.get_roles(frappe.session.user)):
		columns = [_("Item") + ":Link/Item:125", _("Item Name") + "::200", _("Actual Qty") + ":Float:75",  _("UOM") + ":Link/UOM:65", 
			_("Warehouse") + ":Link/Warehouse:125", _("Location") + "::80", _("Sales Avg/30d") + ":Float:100",_("Age Days") + "::70",
			_("Sales Price List") + "::240",
			_("Valuation Rate") + ":Currency:80", _("Last Purchase Rate") + ":Currency:90",
			_("Brand") + ":Link/Brand:100", _("Item Group") + ":Link/Item Group:125", _("Description") + "::150"]
			#_("Purchase Price List") + "::180", _("BOM Rate") + ":Currency:90"]
	else:
		columns = [_("Item") + ":Link/Item:125", _("Item Name") + "::200", _("Actual Qty") + ":Float:75",  _("UOM") + ":Link/UOM:65", 
			_("Warehouse") + ":Link/Warehouse:125", _("Location") + "::80", _("Sales Avg/30d") + "::100",_("Age Days") + "::70",
			_("Sales Price List") + "::240",
			#_("Valuation Rate") + ":Currency:80", _("Last Purchase Rate") + ":Currency:90",
			_("Brand") + ":Link/Brand:100", _("Item Group") + ":Link/Item Group:125", _("Description") + "::150"]	
			#_("Purchase Price List") + "::180", _("BOM Rate") + ":Currency:90"]

	return columns

def get_conditions(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("it.item_code=%(item_code)s")

	#if not filters.get("company"):
	#	filters.get("company") = frappe.defaults.get_user_default("Company")

	if filters.get("company"):
		conditions.append("wh.company=%(company)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_item_details(filters):
	"""returns all items details"""

	item_map = {}

	if "location_bin" not in frappe.db.get_table_columns("Item"):

		item_map = frappe.db.sql("""select it.name, 
			(select cast(avg(si_item.stock_qty) as unsigned) as avg_qty from `tabSales Invoice Item` si_item
			inner join `tabSales Invoice` si on si.name=si_item.parent where si_item.item_code=it.item_code 
			and si_item.stock_uom=it.stock_uom and si_item.warehouse=bin.warehouse 
			and si.docstatus=1 and si.posting_date between date_add(curdate(),INTERVAL -30 DAY) and curdate()) as avg_qty,

			(select rate from `tabPurchase Invoice` pi join `tabPurchase Invoice Item` pi_item on pi.name=pi_item.parent 
			where pi_item.item_code=it.item_code and pi_item.stock_uom=it.stock_uom 
			and pi.docstatus=1 order by pi.posting_date desc limit 1) as last_purchase_rate,

		it.item_group, it.brand, it.item_name, "" as location_bin, it.description, bin.actual_qty, bin.warehouse, wh.company,
		it.stock_uom, bin.valuation_rate from `tabItem` it left join `tabBin` bin on (it.name=bin.item_code and it.stock_uom = bin.stock_uom) 
		left join `tabWarehouse` wh on wh.name=bin.warehouse 
		where it.is_stock_item=1 and it.disabled <> 1 {item_conditions} order by it.item_code, it.item_group"""\
		.format(item_conditions=get_conditions(filters)),filters, as_dict=1)
	else:
		item_map = frappe.db.sql("""select it.name, 
			(select cast(avg(si_item.stock_qty) as unsigned) as avg_qty from `tabSales Invoice Item` si_item
			inner join `tabSales Invoice` si on si.name=si_item.parent where si_item.item_code=it.item_code 
			and si_item.stock_uom=it.stock_uom and si_item.warehouse=bin.warehouse 
			and si.docstatus=1 and si.posting_date between date_add(curdate(),INTERVAL -30 DAY) and curdate()) as avg_qty,

			(select rate from `tabPurchase Invoice` pi join `tabPurchase Invoice Item` pi_item on pi.name=pi_item.parent 
			where pi_item.item_code=it.item_code and pi_item.stock_uom=it.stock_uom 
			and pi.docstatus=1 order by pi.posting_date desc limit 1) as last_purchase_rate,

		it.item_group, it.brand, it.item_name, it.description, it.location_bin, bin.actual_qty, bin.warehouse, wh.company,
		it.stock_uom, bin.valuation_rate from `tabItem` it left join `tabBin` bin on (it.name=bin.item_code and it.stock_uom = bin.stock_uom) 
		left join `tabWarehouse` wh on wh.name=bin.warehouse 
		where it.is_stock_item=1 and it.disabled <> 1 {item_conditions} order by it.item_code, it.item_group"""\
		.format(item_conditions=get_conditions(filters)),filters, as_dict=1)
	

	#print item_map

	return item_map

def get_avg_sales_qty(item_code):
	"""Get average sales qty in last 30 days of an item"""

	sales_avg = {}

	for i in frappe.db.sql("""select cast(avg(si_item.qty) as unsigned) as avg_qty from `tabSales Invoice` si join `tabSales Invoice Item` si_item on si.name=si_item.parent
		where si.posting_date between date_add(si.posting_date,INTERVAL -30 DAY) and curdate() and si_item.item_code=%s""", item_code,as_dict=1):
		sales_avg.setdefault(item_code,i.avg_qty)

	return sales_avg.get(item_code,0)

def get_pl_conditions(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("ip.item_code=%(item_code)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_price_list(filters):
	"""Get selling & buying price list of every item"""

	rate = {}

	price_list = frappe.db.sql("""select ip.item_code, ip.buying, ip.selling,
		concat(ifnull(cu.symbol,ip.currency), " ", FORMAT(ip.price_list_rate,2), " - ", ip.price_list) as price
		from `tabItem Price` ip, `tabPrice List` pl, `tabCurrency` cu
		where ip.price_list=pl.name and pl.currency=cu.name and pl.enabled=1 and ip.selling=1 {pl_conditions}"""\
		.format(pl_conditions=get_pl_conditions(filters)), filters, as_dict=1)

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
						where po.name = po_item.parent and po.docstatus = 1 and po_item.item_code='{item}' order by po.transaction_date desc limit 1)
						union
						(select
							pr_item.item_code,
							pr_item.item_name,
							pr.posting_date,
							pr_item.base_price_list_rate,
							pr_item.discount_percentage,
							pr_item.base_rate
						from `tabPurchase Receipt` pr, `tabPurchase Receipt Item` pr_item
						where pr.name = pr_item.parent and pr.docstatus = 1 and pr_item.item_code='{item}' order by pr.posting_date desc limit 1)
						union
						(select
							pi_item.item_code,
							pi_item.item_name,
							pi.posting_date,
							pi_item.base_price_list_rate,
							pi_item.discount_percentage,
							pi_item.base_rate
						from `tabPurchase Invoice` pi, `tabPurchase Invoice Item` pi_item
						where pi.name = pi_item.parent and pi.docstatus = 1 and pi_item.item_code='{item}' order by pi.posting_date desc limit 1)
				) result
				order by result.item_code asc, result.posting_date desc) result_wrapper
				group by item_code, posting_date order by posting_date desc""".format( item = item_code )

	#if item_code == 'GC001':
	#	frappe.msgprint(query)

	for idx, d in enumerate (frappe.db.sql(query, as_dict=1)):
		if idx==0:
			item_last_purchase_rate_map.setdefault(d.item_code, d.base_rate)
 
	#print item_last_purchase_rate_map

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

	#print bin_map
			
	return bin_map

