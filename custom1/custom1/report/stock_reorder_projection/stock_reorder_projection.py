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

	avg_daily_outgoing = 0
	diff = ((getdate(filters.get("to_date")) - getdate(filters.get("from_date"))).days)+1
	if diff <= 0:
		frappe.throw(_("'From Date' must be after 'To Date'"))

	columns = get_columns(filters)
	items = get_item_info(filters)
	return_item_map = get_return_items(condition, filters)
	delivered_item_map = get_delivered_items(condition, filters)
	total_outgoing = 0
	total_return = 0

	data = []
	for item in sorted(items):
		if delivered_item_map.get(item.name) is not None:
			#qty_map = {k:v for k,v in delivered_item_map.items() if k == item.name and delivered_item_map[k]["warehouse"]==item.warehouse}
			#total_outgoing = flt(qty_map.get(item.name,{}).get("si_qty",0))
			#total_outgoing = flt(delivered_item_map.get(item.name,{}).get("si_qty",0))

			if filters.get("group_by_warehouse"):
				total_outgoing = flt(delivered_item_map.get(item.name,{}).get(item.warehouse,{}).get("qty",0))
			else:
				total_outgoing = flt(delivered_item_map.get(item.name,{}).get("qty",0))

		if return_item_map.get(item.name) is not None:
			if filters.get("group_by_warehouse"):
				total_return = flt(return_item_map.get(item.name,{}).get(item.warehouse,{}).get("qty",0))
			else:
				total_return = flt(return_item_map.get(item.name,{}).get("qty",0))

			#total_return = flt(return_item_map.get(item.name,{}).get("return_qty",0))
			#for k,v in return_item_map.items():
			#	if k == item.name and return_item_map[k]["warehouse"]==item.warehouse:
			#		return_map = return_item_map[k]
			#		total_return = flt(return_map.return_qty)
	
		reorder_level = flt(total_outgoing) - flt(total_return) - flt(item.actual_qty)

		if filters.get("group_by_warehouse"):
			data.append([item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom, item.warehouse,
				total_outgoing, total_return, item.actual_qty,
				 reorder_level])
		else:
			data.append([item.name, item.item_name, item.description, item.item_group, item.brand, item.stock_uom,
				total_outgoing, total_return, item.actual_qty,
				 reorder_level])

		total_outgoing = 0
		total_return = reorder_level = 0

	return columns , data

def get_columns(filters=None):
	if filters.get("group_by_warehouse"):
		return[
			_("Item") + ":Link/Item:120", _("Item Name") + ":Data:120", _("Description") + "::160",
			_("Item Group") + ":Link/Item Group:120", _("Brand") + ":Link/Brand:100", _("UOM") + ":Link/UOM:60",
			#_("Safety Stock") + ":Float:160", _("Lead Time Days") + ":Float:120", _("Consumed") + ":Float:120",
			#_("Delivered") + ":Float:120", _("Total Outgoing") + ":Float:120", _("Avg Daily Outgoing") + ":Float:160",
			_("Warehouse") + ":Link/Warehouse:120",
			_("Total Outgoing") + ":Float:120", _("Total Return") + ":Float:120", _("Actual Qty") + ":Float:120",
			_("Reorder Level") + ":Float:120"
		]
	else:
		return[
			_("Item") + ":Link/Item:120", _("Item Name") + ":Data:120", _("Description") + "::160",
			_("Item Group") + ":Link/Item Group:120", _("Brand") + ":Link/Brand:100", _("UOM") + ":Link/UOM:60",
			#_("Safety Stock") + ":Float:160", _("Lead Time Days") + ":Float:120", _("Consumed") + ":Float:120",
			#_("Delivered") + ":Float:120", _("Total Outgoing") + ":Float:120", _("Avg Daily Outgoing") + ":Float:160",
			_("Total Outgoing") + ":Float:120", _("Total Return") + ":Float:120", _("Actual Qty") + ":Float:120",
			_("Reorder Level") + ":Float:120"
		]

def get_item_info(filters):
	if filters.get("group_by_warehouse"):
		return frappe.db.sql("""select it.name, it.stock_uom, sum(bin.actual_qty) as actual_qty, it.item_name, it.description, item_group, brand, bin.warehouse
			from `tabItem` it, `tabBin` bin Where it.item_code=bin.item_code and it.disabled=0 group by
			it.name, it.stock_uom, bin.warehouse""", as_dict=1) #it.item_name, it.description, item_group, brand""", as_dict=1)
	else:
		return frappe.db.sql("""select it.name, it.stock_uom, sum(bin.actual_qty) as actual_qty, it.item_name, it.description, item_group, brand
			from `tabItem` it, `tabBin` bin Where it.item_code=bin.item_code and it.disabled=0 group by
			it.name, it.stock_uom""", as_dict=1) #it.item_name, it.description, item_group, brand""", as_dict=1)

def get_consumed_items(condition):

	cn_items = frappe.db.sql("""select se_item.item_code,
				sum(se_item.actual_qty) as 'consume_qty'
		from `tabStock Entry` se, `tabStock Entry Detail` se_item
		where se.name = se_item.parent and se.docstatus = 1
		and ifnull(se_item.t_warehouse, '') = '' %s
		group by se_item.item_code""" % (condition), as_dict=1)

	cn_items_map = {}
	for item in cn_items:
		cn_items_map.setdefault(item.item_code, item.consume_qty)

	return cn_items_map

def get_return_items(condition, filters=None):
	si_items = {}

	if filters.get("group_by_warehouse"):
		si_items = frappe.db.sql("""select result.item_code, result.warehouse, sum(si_qty) as qty from (
						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabDelivery Note` si, `tabDelivery Note Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return = 1 %s
						group by si_item.item_code, si_item.warehouse

						union all

						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabSales Invoice` si, `tabSales Invoice Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return = 1 and
						si.update_stock = 1 and ifnull(si_item.delivery_note,'') = '' %s
						group by si_item.item_code, si_item.warehouse) result
				group by result.item_code, result.warehouse""" % (condition,condition), as_dict=1)
	else:
		si_items = frappe.db.sql("""select result.item_code, sum(si_qty) as qty from (
						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabDelivery Note` si, `tabDelivery Note Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return = 1 %s
						group by si_item.item_code, si_item.warehouse

						union all

						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabSales Invoice` si, `tabSales Invoice Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return = 1 and
						si.update_stock = 1 and ifnull(si_item.delivery_note,'') = '' %s
						group by si_item.item_code, si_item.warehouse) result
				group by result.item_code""" % (condition,condition), as_dict=1)

	#dn_items = frappe.db.sql("""select si_item.item_code, sum(abs(si_item.qty)) as return_qty
	#	from `tabDelivery Note` si, `tabDelivery Note Item` si_item
	#	where si.name = si_item.parent and si.docstatus = 1 and si.is_return = 1 %s
	#	group by si_item.item_code""" % (condition), as_dict=1)

	dn_item_map = {}

	for item in si_items:
		if filters.get("group_by_warehouse"):
			dn_item_map.setdefault(item.item_code, {}).setdefault(item.warehouse, item)
		else:
			dn_item_map.setdefault(item.item_code, item)

	#for item in dn_items:
	#	dn_item_map.setdefault(item.item_code, item)

	return dn_item_map

def get_delivered_items(condition, filters=None):
	si_items = {}

	sql = ("""select result.item_code, result.warehouse, sum(si_qty) as qty from (
						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabDelivery Note` si, `tabDelivery Note Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 %s
						group by si_item.item_code, si_item.warehouse

						union all

						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabSales Invoice` si, `tabSales Invoice Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 and
						si.update_stock = 1 %s
						group by si_item.item_code, si_item.warehouse) result
				group by result.item_code, result.warehouse""" % (condition,condition))
	

	if filters.get("group_by_warehouse"):
		si_items = frappe.db.sql("""select result.item_code, result.warehouse, sum(si_qty) as qty from (
						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabDelivery Note` si, `tabDelivery Note Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 %s
						group by si_item.item_code, si_item.warehouse

						union all

						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabSales Invoice` si, `tabSales Invoice Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 and
						si.update_stock = 1 and ifnull(si_item.delivery_note,'') = '' %s
						group by si_item.item_code, si_item.warehouse) result
				group by result.item_code, result.warehouse""" % (condition,condition), as_dict=1)

	else:
		si_items = frappe.db.sql("""select result.item_code, sum(si_qty) as qty from (
						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabDelivery Note` si, `tabDelivery Note Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 %s
						group by si_item.item_code, si_item.warehouse

						union all

						select si_item.item_code, si_item.warehouse, sum(si_item.qty) as si_qty
						from `tabSales Invoice` si, `tabSales Invoice Item` si_item
						where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 and
						si.update_stock = 1 and ifnull(si_item.delivery_note,'') = '' %s
						group by si_item.item_code, si_item.warehouse) result
				group by result.item_code""" % (condition,condition), as_dict=1)

	#dn_items = frappe.db.sql("""select si_item.item_code, sum(si_item.qty) as si_qty
	#	from `tabDelivery Note` si, `tabDelivery Note Item` si_item
	#	where si.name = si_item.parent and si.docstatus = 1 and si.is_return != 1 %s
	#	group by si_item.item_code""" % (condition), as_dict=1)

	dn_item_map = {}

	for item in si_items:
		if filters.get("group_by_warehouse"):
			dn_item_map.setdefault(item.item_code, {}).setdefault(item.warehouse,item)
		else:
			dn_item_map.setdefault(item.item_code, item)

	#for item in dn_items:
	#	dn_item_map.setdefault(item.item_code, item)

	return dn_item_map

def get_condition(filters):
	conditions = ""
	if filters.get("from_date") and filters.get("to_date"):
		conditions += " and si.posting_date between '%s' and '%s' " % (filters["from_date"],filters["to_date"])
	else:
		frappe.throw(_("From and To dates required"))
	return conditions
