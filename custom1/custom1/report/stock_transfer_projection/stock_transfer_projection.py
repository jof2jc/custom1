# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import getdate, flt, cstr

def execute(filters=None):
	if not filters: filters = {}
	float_preceision = frappe.db.get_default("float_preceision")

	condition =get_condition(filters)
	tr_condition =get_transfered_condition(filters)

	avg_daily_outgoing = 0
	diff = ((getdate(filters.get("to_date")) - getdate(filters.get("from_date"))).days)+1
	if diff <= 0:
		frappe.throw(_("'From Date' must be after 'To Date'"))

	columns = get_columns()
	items = get_item_info()
	return_item_map = get_return_items(condition)
	delivered_item_map = get_delivered_items(condition)
	transfered_item_map = get_transfered_qty(tr_condition)

	total_outgoing = 0
	total_return = 0
	total_transfered = 0
	to_transfered = 0

	data = []
	for item in sorted(items):
		if delivered_item_map.get(item.name) is not None:
			#qty_map = {k:v for k,v in delivered_item_map.items() if k == item.name and delivered_item_map[k]["warehouse"]==item.warehouse}
			#total_outgoing = flt(qty_map.get(item.name,{}).get("si_qty",0))
			total_outgoing = flt(delivered_item_map.get(item.name,{}).get("si_qty",0))
			#frappe.msgprint(cstr(qty_map.si_qty))

		if return_item_map.get(item.name) is not None:
			total_return = flt(return_item_map.get(item.name,{}).get("return_qty",0))
			#for k,v in return_item_map.items():
			#	if k == item.name and return_item_map[k]["warehouse"]==item.warehouse:
			#		return_map = return_item_map[k]
			#		total_return = flt(return_map.return_qty)
	
		if transfered_item_map.get(item.name) is not None:
			total_transfered = flt(transfered_item_map.get(item.name,{}).get("transfered_qty",0))

		to_transfer = flt(total_outgoing) - flt(total_return) - flt(total_transfered)

		data.append([item.name, item.stock_uom,
				total_outgoing, total_return, total_transfered,
			 to_transfer, item.toko, item.gudang, item.item_name, item.description, item.item_group, item.brand])
		total_outgoing = 0
		total_return = total_transfered = to_transfer = 0

	return columns , data

def get_columns():
	return[
			_("Item") + ":Link/Item:120", _("UOM") + ":Link/UOM:60",
			#_("Safety Stock") + ":Float:160", _("Lead Time Days") + ":Float:120", _("Consumed") + ":Float:120",
			#_("Delivered") + ":Float:120", _("Total Outgoing") + ":Float:120", _("Avg Daily Outgoing") + ":Float:160",
			_("Total Outgoing") + ":Float:100", _("Total Return") + ":Float:100", _("Transfered Qty") + ":Float:100",
			_("To Transfer") + ":Float:100", _("Actual Toko") + ":Float:100", _("Actual Gudang") + ":Float:100",
			_("Item Name") + ":Data:120", _("Description") + "::160",
			_("Item Group") + ":Link/Item Group:120", _("Brand") + ":Link/Brand:100"
	]

def get_item_info():
	return frappe.db.sql("""select item_code as name, stock_uom, sum(ifnull(toko,0)) as toko, sum(ifnull(gudang,0)) as gudang,
				description, item_name, brand, item_group from (
					select it.item_code, it.stock_uom, 
					(case when bin.warehouse like '%Glodok%' then sum(ifnull(actual_qty,0)) END) as toko, 
					(case when bin.warehouse like '%Gudang%' then sum(ifnull(actual_qty,0)) END) as gudang,
					it.item_name, it.description, item_group, brand
					from `tabItem` it, `tabBin` bin Where it.item_code=bin.item_code group by
					it.name, bin.warehouse, it.stock_uom, it.item_name, it.description, item_group, brand
				) result group by name, stock_uom""", as_dict=1)

def get_transfered_qty(condition):

	cn_items = frappe.db.sql("""select se_item.item_code,
				sum(se_item.qty) as 'transfered_qty'
		from `tabStock Entry` se, `tabStock Entry Detail` se_item
		where se.name = se_item.parent and se.docstatus = 1 and se.purpose='Material Transfer' %s
		group by se_item.item_code""" % (condition), as_dict=1)

	cn_items_map = {}
	for item in cn_items:
		cn_items_map.setdefault(item.item_code, item)

	return cn_items_map

def get_return_items(condition):
	si_items = frappe.db.sql("""select si_item.item_code, sum(abs(si_item.qty)) as return_qty
		from `tabSales Invoice` si, `tabSales Invoice Item` si_item
		where si.name = si_item.parent and si.docstatus = 1 and si.is_return = 1 and
		si.update_stock = 1 %s
		group by si_item.item_code""" % (condition), as_dict=1)


	dn_item_map = {}

	for item in si_items:
		dn_item_map.setdefault(item.item_code, item)

	return dn_item_map

def get_delivered_items(condition):
	sql = ("""select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
		from `tabSales Invoice` si, `tabSales Invoice Item` si_item
		where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 and
		si.update_stock = 1 and si_item.item_code = 'RE 03' %s
		group by si_item.item_code, si_item.warehouse""" % (condition))

	si_items = frappe.db.sql("""select si_item.item_code, sum(si_item.qty) as si_qty
		from `tabSales Invoice` si, `tabSales Invoice Item` si_item
		where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 and
		si.update_stock = 1 %s
		group by si_item.item_code""" % (condition), as_dict=1)

	dn_item_map = {}

	for item in si_items:
		dn_item_map.setdefault(item.item_code, item)

	return dn_item_map

def get_condition(filters):
	conditions = ""

	if filters.get("warehouse"):
		conditions += " and si_item.warehouse='%s' " % (filters["warehouse"])

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and posting_date between '%s' and '%s' " % (filters["from_date"],filters["to_date"])
	else:
		frappe.throw(_("From and To dates required"))
	return conditions

def get_transfered_condition(filters):
	conditions = ""
	if filters.get("warehouse"):
		conditions += " and se_item.t_warehouse='%s' " % (filters["warehouse"])
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and posting_date between '%s' and '%s' " % (filters["from_date"],filters["to_date"])
	else:
		frappe.throw(_("From and To dates required"))
	return conditions
