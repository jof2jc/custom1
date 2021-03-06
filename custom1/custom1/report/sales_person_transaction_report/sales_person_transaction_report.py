# Copyright (c) 2013, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)
	entries = get_entries(filters)	
	data = [] 
	
	if filters.get("group_by")=="Item Code":
	        for d in entries:
			data.append([
				d.name, d.customer, d.territory, d.posting_date, d.item_code, d.item_group, d.brand,
				d.qty, d.base_net_amount, d.sales_person, d.allocated_percentage, d.contribution_amt
		])
        else:
	        for d in entries:
			data.append([
			d.sales_person, d.brand,d.qty, d.amount
		])

	return columns, data

def get_columns(filters):
	if not filters.get("doc_type"):
		msgprint(_("Please select the document type first"), raise_exception=1)

	if filters.get("group_by")=="Item Code":
	        return [filters["doc_type"] + ":Link/" + filters["doc_type"] + ":140",
		_("Customer") + ":Link/Customer:140", _("Territory") + ":Link/Territory:100", _("Posting Date") + ":Date:100",
		_("Item Code") + ":Link/Item:120", _("Item Group") + ":Link/Item Group:120",
		_("Brand") + ":Link/Brand:120", _("Qty") + ":Float:100", _("Amount") + ":Currency:120",
		_("Sales Person") + ":Link/Sales Person:140", _("Contribution %") + ":Float:110",
		_("Contribution Amount") + ":Currency:140"]
	else:
	        return [_("Sales Person") + ":Link/Sales Person:140", ("Brand") + ":Link/Brand:120", _("Qty") + ":Float:100", 
			_("Amount") + ":Currency:200"]


def get_entries(filters):
	date_field = filters["doc_type"] == "Sales Order" and "transaction_date" or "posting_date"
	conditions, values = get_conditions(filters, date_field)
        if filters.get("group_by")=="Item Code":
		entries = frappe.db.sql("""select dt.name, dt.customer, dt.territory, dt.%s as posting_date,
			dt_item.item_code, it.item_group, it.brand, dt_item.qty, dt_item.base_net_amount, st.sales_person,
			st.allocated_percentage, dt_item.base_net_amount*st.allocated_percentage/100 as contribution_amt
			from `tab%s` dt, `tab%s Item` dt_item, `tabSales Team` st, `tabItem` it
			where st.parent = dt.name and dt.name = dt_item.parent and dt_item.item_code = it.item_code and st.parenttype = %s
			and dt.docstatus = 1 %s order by st.sales_person, dt.name desc""" %
			(date_field, filters["doc_type"], filters["doc_type"], '%s', conditions),
			tuple([filters["doc_type"]] + values), as_dict=1)
        else:
                entries = frappe.db.sql("""select st.sales_person, it.brand, sum(dt_item.qty) as qty, sum(dt_item.base_net_amount) as amount
			from `tab%s` dt, `tab%s Item` dt_item, `tabSales Team` st, `tabItem` it
			where st.parent = dt.name and dt.name = dt_item.parent and dt_item.item_code = it.item_code and st.parenttype = %s
			and dt.docstatus = 1 %s group by st.sales_person, it.brand order by st.sales_person""" %
                        (filters["doc_type"], filters["doc_type"], '%s', conditions),
			tuple([filters["doc_type"]] + values), as_dict=1)

	return entries

def get_conditions(filters, date_field):
	conditions = [""]
	values = []
	
	for field in ["company", "customer", "territory"]:
		if filters.get(field):
			conditions.append("dt.{0}=%s".format(field))
			values.append(filters[field])
			
	if filters.get("sales_person"):
		conditions.append("st.sales_person=%s")
		values.append(filters["sales_person"])
		
	if filters.get("from_date"):
		conditions.append("dt.{0}>=%s".format(date_field))
		values.append(filters["from_date"])
		
	if filters.get("to_date"):
		conditions.append("dt.{0}<=%s".format(date_field))
		values.append(filters["to_date"])

	items = get_items(filters)
	if items:
		conditions.append("dt_item.item_code in (%s)" % ', '.join(['%s']*len(items)))
		values += items

	return " and ".join(conditions), values

def get_items(filters):
	if filters.get("item_group"): key = "item_group"
	elif filters.get("brand"): key = "brand"
	else: key = ""

	items = []
	if key:
		items = frappe.db.sql_list("""select name from tabItem where %s = %s""" %
			(key, '%s'), (filters[key]))

	return items



