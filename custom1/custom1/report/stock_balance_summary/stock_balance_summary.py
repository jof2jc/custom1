# Copyright (c) 2013, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)
	
	

	data = []

	if filters.get("group_by")=="Item Code":
		iwb_map = get_item_warehouse_map(filters)
		for company in sorted(iwb_map):
			for item in sorted(iwb_map[company]):
				for wh in sorted(iwb_map[company][item]):
					qty_dict = iwb_map[company][item][wh]
					data.append([item, qty_dict.item_name,
						qty_dict.item_group,
						qty_dict.brand,
						qty_dict.description, wh,
						qty_dict.stock_uom, qty_dict.opening_qty,
						(qty_dict.opening_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), qty_dict.in_qty,
						(qty_dict.in_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), qty_dict.out_qty,
						(qty_dict.out_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), qty_dict.bal_qty,
						(qty_dict.bal_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), 
						(qty_dict.val_rate if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0),
						company
					])
	else:
		iwb_map = get_item_warehouse_map_bybrand(filters)
		for company in sorted(iwb_map):
			for brand in sorted(iwb_map[company]):
				for stock_uom in sorted(iwb_map[company][brand]):
					for wh in sorted(iwb_map[company][brand][stock_uom]):
						qty_dict = iwb_map[company][brand][stock_uom][wh]
						data.append([qty_dict.brand,
							wh,
							qty_dict.stock_uom, qty_dict.opening_qty,
							(qty_dict.opening_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), qty_dict.in_qty,
							(qty_dict.in_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), qty_dict.out_qty,
							(qty_dict.out_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0), qty_dict.bal_qty,
							(qty_dict.bal_val if "Accounts Manager" in frappe.get_roles(frappe.session.user) else 0.0),
							company
						])	

	return columns, data

def get_columns(filters):
	"""return columns based on filters"""

	if filters.get("group_by")=="Item Code":
		columns = ["Item:Link/Item:100", "Item Name::150", "Item Group::100", "Brand::90", \
		"Description::140", "Warehouse:Link/Warehouse:100", "Stock UOM:Link/UOM:90", "Opening Qty:Float:100", \
		"Opening Value:Float:110", "In Qty:Float:80", "In Value:Float:80", "Out Qty:Float:80", \
		"Out Value:Float:80", "Balance Qty:Float:100", "Balance Value:Float:100", \
		"Valuation Rate:Float:90", "Company:Link/Company:100"]
	else:
		columns = ["Brand::90", \
		"Warehouse:Link/Warehouse:100", "Stock UOM:Link/UOM:90", "Opening Qty:Float:100", \
		"Opening Value:Float:110", "In Qty:Float:80", "In Value:Float:80", "Out Qty:Float:80", \
		"Out Value:Float:80", "Balance Qty:Float:100", "Balance Value:Float:100", \
		"Company:Link/Company:100"]

	return columns

def get_conditions(filters):
	conditions = ""
	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))

	if filters.get("to_date"):
		conditions += " and sle.posting_date <= '%s'" % filters["to_date"]
	else:
		frappe.throw(_("'To Date' is required"))

	if filters.get("item_group"):
		conditions += " and it.item_group = '%s'" % filters["item_group"]

	if filters.get("company"):
		conditions += " and sle.company = '%s'" % filters["company"]

	if filters.get("warehouse"):
		conditions += " and sle.warehouse = '%s'" % filters["warehouse"]

	if filters.get("brand"):
		conditions += " and it.brand = '%s'" % filters["brand"]


	return conditions

#get all details
def get_stock_ledger_entries(filters):
	conditions = get_conditions(filters)
	return frappe.db.sql("""select sle.item_code, it.item_name, it.description, it.item_group, it.brand, it.stock_uom,
	sle.warehouse, sle.posting_date, sle.actual_qty, sle.valuation_rate,
	sle.company, sle.voucher_type, sle.qty_after_transaction, sle.stock_value_difference
		from `tabStock Ledger Entry` sle, `tabItem` it
		where sle.item_code = it.item_code and 
		sle.docstatus < 2 %s order by sle.posting_date, sle.posting_time, sle.name""" %
		conditions, as_dict=1)


def get_item_warehouse_map(filters):
	sle = get_stock_ledger_entries(filters)
	iwb_map = {}

	for d in sle:
		iwb_map.setdefault(d.company, {}).setdefault(d.item_code, {}).\
		setdefault(d.warehouse, frappe._dict({\
				"opening_qty": 0.0, "opening_val": 0.0,
				"in_qty": 0.0, "in_val": 0.0,
				"out_qty": 0.0, "out_val": 0.0,
				"bal_qty": 0.0, "bal_val": 0.0,
				"val_rate": 0.0, "uom": None
			}))
		qty_dict = iwb_map[d.company][d.item_code][d.warehouse]

		qty_dict.item_name = d.item_name
		qty_dict.item_group = d.item_group
		qty_dict.brand = d.brand
		qty_dict.description = d.description
		qty_dict.stock_uom = d.stock_uom

		if d.voucher_type == "Stock Reconciliation":
			qty_diff = flt(d.qty_after_transaction) - qty_dict.bal_qty
		else:
			qty_diff = flt(d.actual_qty)

		value_diff = flt(d.stock_value_difference)
		
		if d.posting_date < getdate(filters["from_date"]):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff
		elif d.posting_date >= getdate(filters["from_date"]) and d.posting_date <= getdate(filters["to_date"]):
			if qty_diff > 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)
				
		qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff 
		qty_dict.bal_val += value_diff

	return iwb_map

def get_item_warehouse_map_bybrand(filters):
	sle = get_stock_ledger_entries(filters)
	iwb_map = {}

	for d in sle:
		iwb_map.setdefault(d.company, {}).setdefault(d.brand, {}).\
		setdefault(d.stock_uom, {}).setdefault(d.warehouse, frappe._dict({\
				"opening_qty": 0.0, "opening_val": 0.0,
				"in_qty": 0.0, "in_val": 0.0,
				"out_qty": 0.0, "out_val": 0.0,
				"bal_qty": 0.0, "bal_val": 0.0,
				"val_rate": 0.0
			}))
		qty_dict = iwb_map[d.company][d.brand][d.stock_uom][d.warehouse]

		qty_dict.brand = d.brand
		qty_dict.stock_uom = d.stock_uom

		if d.voucher_type == "Stock Reconciliation":
			qty_diff = flt(d.qty_after_transaction)
		else:
			qty_diff = flt(d.actual_qty)

		value_diff = flt(d.stock_value_difference)
		
		if d.posting_date < getdate(filters["from_date"]):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff
		elif d.posting_date >= getdate(filters["from_date"]) and d.posting_date <= getdate(filters["to_date"]):
			if qty_diff > 0:
				qty_dict.in_qty += qty_diff
				qty_dict.in_val += value_diff
			else:
				qty_dict.out_qty += abs(qty_diff)
				qty_dict.out_val += abs(value_diff)
				
		qty_dict.val_rate += d.valuation_rate
		qty_dict.bal_qty += qty_diff 
		qty_dict.bal_val += value_diff

	return iwb_map

def get_item_details(filters):
	item_map = {}
	for d in frappe.db.sql("select name, item_name, stock_uom, item_group, brand, \
		description from tabItem", as_dict=1):
		item_map.setdefault(d.name, d)

	return item_map

