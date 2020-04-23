# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, flt, cstr, fmt_money

def execute(filters=None):
	columns = get_columns()
	items = get_items(filters)
	sl_entries = get_stock_ledger_entries(filters, items)
	item_details = get_item_details(items, sl_entries)
	opening_row = get_opening_balance(filters, columns)

	data = []
	party = []

	if opening_row:
		data.append(opening_row)

	for sle in sl_entries:
		party_details = get_party_details(sle.item_code, sle.voucher_type, sle.voucher_no)
		if sle.voucher_type in ("Sales Invoice", "Purchase Invoice", "Purchase Receipt", "Delivery Note"): 
			party = party_details[sle.voucher_no]
		else:	
			party = []

		uoms = item_details[sle.item_code]
		item_detail = {}

		#item_detail = item_details[sle.item_code]

		for k,v in uoms.items():
			if uoms[k]["conversion_factor"] > 1:
				item_detail = uoms[k]
				break
			else:
				item_detail = uoms[k]

		data.append([sle.date, sle.item_code, item_detail.item_name, item_detail.item_group,
			#item_detail.brand, item_detail.description, 
			sle.warehouse, 
			(item_detail.stock_uom + " ~ " + item_detail.uom if item_detail.conversion_factor > 1 else item_detail.stock_uom),#item_detail.stock_uom, 
			flt(sle.actual_qty),
			(flt(sle.actual_qty/item_detail.conversion_factor) if item_detail.conversion_factor > 1 else 0.0), 
			(fmt_money(sle.qty_after_transaction,2) + " ~ " + fmt_money(sle.qty_after_transaction/item_detail.conversion_factor,4) if item_detail.conversion_factor > 1 else fmt_money(sle.qty_after_transaction,2)),
			item_detail.conversion_factor, #item_detail.uom, 
			
			#(sle.actual_qty/item_detail.conversion_factor if item_detail.conversion_factor != 1 else 0.0), #qty
			#(sle.qty_after_transaction/item_detail.conversion_factor if item_detail.conversion_factor != 1 else 0.0), #balance qty
			
			(fmt_money(sle.incoming_rate,2) + " ~ " + fmt_money(sle.incoming_rate*item_detail.conversion_factor,2) if item_detail.conversion_factor > 1 else fmt_money(sle.incoming_rate,2)), #(sle.incoming_rate if sle.actual_qty > 0 else 0.0),
			(fmt_money(sle.valuation_rate,2) + " ~ " + fmt_money(sle.valuation_rate*item_detail.conversion_factor,2) if item_detail.conversion_factor > 1 else fmt_money(sle.valuation_rate,2)), #sle.valuation_rate, 
			#(sle.incoming_rate*item_detail.conversion_factor if item_detail.conversion_factor !=1 else 0.0), #incoming_rate
			#(sle.valuation_rate*item_detail.conversion_factor if item_detail.conversion_factor != 1 else 0.0), #valuation_rate
			
			sle.stock_value, 
			(party.outgoing_rate if party else 0.0), (party.party if party else ""),
			sle.voucher_type, sle.voucher_no,
			sle.batch_no, sle.serial_no, sle.project, sle.company])

	return columns, data

def get_columns():
	columns = [
		_("Date") + ":Datetime:95", _("Item") + ":Link/Item:130",
		_("Item Name") + "::100", _("Item Group") + ":Link/Item Group:100",
		#_("Brand") + ":Link/Brand:100", _("Description") + "::200",
		_("Warehouse Stage") + ":Link/Warehouse:100", _("Stock UOM") + "::100",
		_("Qty") + ":Float:75", {"label": _("Converted Qty"),"fieldtype": "Float", "width": 75, "precision": 4}, 
		_("Balance Qty") + "::140", _("Conversion Factor") + ":Float:75",

		#_("#UOM") + ":Link/UOM:75", {"label": _("#Qty"),"fieldtype": "Float", "width": 50, "precision": 4}, 
		#{"label": _("#Balance Qty"),"fieldtype": "Float", "width": 75, "precision": 4},

		{"label": _("Incoming Rate"), "fieldtype": "Data", "width": 160},
			#"options": "Company:company:default_currency"},
		{"label": _("Valuation Rate"), "fieldtype": "Data", "width": 160},
			#"options": "Company:company:default_currency"},
		
		#{"label": _("#Incoming Rate"), "fieldtype": "Currency", "width": 110,
		#	"options": "Company:company:default_currency"},
		#{"label": _("#Valuation Rate"), "fieldtype": "Currency", "width": 110,
		#	"options": "Company:company:default_currency"},
		
		{"label": _("Balance Value"), "fieldtype": "Currency", "width": 120,
			"options": "Company:company:default_currency"},
		{"label": _("Outgoing Rate"), "fieldtype": "Currency", "width": 110,
			"options": "Company:company:default_currency"},
		_("Customer or Supplier") + ":Dynamic Link/Party Type:150",
		_("Voucher Type") + "::110",
		_("Voucher #") + ":Dynamic Link/" + _("Voucher Type") + ":100",
		_("Batch") + ":Link/Batch:100",
		_("Serial #") + ":Link/Serial No:100",
		_("Project") + ":Link/Project:100",
		{"label": _("Company"), "fieldtype": "Link", "width": 110,
			"options": "company", "fieldname": "company"}
	]

	return columns

def get_party_details(item_code,voucher_type,voucher_no):
	party_details = {}

	params = {
		'item_code' : item_code,
		'voucher_no' : voucher_no,
		'voucher_type' : voucher_type
	}

	if voucher_type == "Sales Invoice":
		for party in frappe.db.sql("""select dt_item.parent, dt_item.item_code, dt.customer as party, 'Customer' as party_type, rate as outgoing_rate
			from `tabSales Invoice` dt, `tabSales Invoice Item` dt_item
			where dt.name = dt_item.parent {party_conditions} limit 1""".format(party_conditions=get_party_conditions(item_code, voucher_no)), params, as_dict=1):
			party_details.setdefault(party.parent, party) 
	elif voucher_type == "Delivery Note":
		for party in frappe.db.sql("""select dt_item.parent, dt_item.item_code, dt.customer as party, 'Customer' as party_type, rate as outgoing_rate
			from `tabDelivery Note` dt, `tabDelivery Note Item` dt_item
			where dt.name = dt_item.parent {party_conditions} limit 1""".format(party_conditions=get_party_conditions(item_code, voucher_no)), params, as_dict=1):
			party_details.setdefault(party.parent, party)
	elif voucher_type == "Purchase Invoice":
		for party in frappe.db.sql("""select dt_item.parent, dt_item.item_code, dt.supplier as party, 'Supplier' as party_type, 0.0 as outgoing_rate
			from `tabPurchase Invoice` dt, `tabPurchase Invoice Item` dt_item
			where dt.name = dt_item.parent and dt_item.parent = %(voucher_no)s and dt_item.item_code = %(item_code)s""", params, as_dict=1):
			party_details.setdefault(party.parent, party)
	elif voucher_type == "Purchase Receipt":
		for party in frappe.db.sql("""select dt_item.parent, dt_item.item_code, dt.supplier as party, 'Supplier' as party_type, 0.0 as outgoing_rate
			from `tabPurchase Receipt` dt, `tabPurchase Receipt Item` dt_item
			where dt.name = dt_item.parent and dt_item.parent = %(voucher_no)s and dt_item.item_code = %(item_code)s""", params, as_dict=1):
			party_details.setdefault(party.parent, party)

	return party_details

def get_party_conditions(item_code, voucher_no):
	conditions = []
	#parent_item = ""

	parent_item = frappe.db.sql("""Select pb.name from `tabProduct Bundle` pb, `tabProduct Bundle Item` pi 
			Where pb.name=pi.parent and pi.item_code=%s limit 1""", item_code, as_dict=0)
	#if voucher_no == "MS/17/10/380" and item_code in ("EASY T LANCET STRIP MEDILANCE@","EASY TOUCH GLUKOSA STRIP@"):
	#	frappe.throw(_("Item {0}, Parent is {1}").format(item_code, parent_item))

	if item_code and not parent_item:
		if frappe.db.get_value("Item",item_code,"is_stock_item"):
			conditions.append("dt_item.item_code=%(item_code)s")

	if voucher_no:
		conditions.append("dt_item.parent=%(voucher_no)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""


def get_stock_ledger_entries(filters, items):
	item_conditions_sql = ''
	repack_condition_sql = ''

	if items:
		item_conditions_sql = 'and sle.item_code in ({})'\
			.format(', '.join(['"' + frappe.db.escape(i) + '"' for i in items]))
	
	if filters.get("repack_only"):
		repack_condition_sql = ' and ste.purpose="Repack"'			
	
	return frappe.db.sql("""select concat_ws(" ", sle.posting_date, sle.posting_time) as date,
			item_code, warehouse, actual_qty, qty_after_transaction, incoming_rate, valuation_rate,
			stock_value, voucher_type, voucher_no, batch_no, serial_no, sle.company, sle.project
		from `tabStock Ledger Entry` sle left outer join `tabStock Entry` ste on ste.name=sle.voucher_no
		where sle.company = %(company)s and
			sle.posting_date between %(from_date)s and %(to_date)s
			{repack_condition_sql}
			{sle_conditions}
			{item_conditions_sql}
			order by sle.posting_date asc, sle.posting_time asc, sle.name asc"""\
		.format(
			sle_conditions=get_sle_conditions(filters),
			item_conditions_sql = item_conditions_sql,
			repack_condition_sql = repack_condition_sql
		), filters, as_dict=1)

def get_items(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("item.name=%(item_code)s")
	else:
		if filters.get("brand"):
			conditions.append("item.brand=%(brand)s")
		if filters.get("item_group"):
			conditions.append(get_item_group_condition(filters.get("item_group")))

	items = []
	if conditions:
		items = frappe.db.sql_list("""select name from `tabItem` item where {}"""
			.format(" and ".join(conditions)), filters)
	return items

def get_item_details(items, sl_entries):
	item_details = {}
	if not items:
		items = list(set([d.item_code for d in sl_entries]))

	if not items:
		return item_details

	for item in frappe.db.sql("""
		select it.name, it.item_name, it.description, item_group, brand, stock_uom, ifnull(uom.uom,'') as uom, ifnull(uom.conversion_factor,0) as conversion_factor
		from `tabItem` it left join `tabUOM Conversion Detail` uom on it.name=uom.parent
		where it.name in ({0})
		""".format(', '.join(['"' + frappe.db.escape(i,percent=False) + '"' for i in items])), as_dict=1):
			item_details.setdefault(item.name, {}).setdefault(item.uom, item)

	return item_details

def get_sle_conditions(filters):
	conditions = []
	if filters.get("warehouse"):
		warehouse_condition = get_warehouse_condition(filters.get("warehouse"))
		if warehouse_condition:
			conditions.append(warehouse_condition)
	if filters.get("voucher_no"):
		conditions.append("voucher_no=%(voucher_no)s")
	if filters.get("batch_no"):
		conditions.append("batch_no=%(batch_no)s")
	if filters.get("project"):
		conditions.append("project=%(project)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_opening_balance(filters, columns):
	if not (filters.item_code and filters.warehouse and filters.from_date):
		return

	from erpnext.stock.stock_ledger import get_previous_sle
	last_entry = get_previous_sle({
		"item_code": filters.item_code,
		"warehouse_condition": get_warehouse_condition(filters.warehouse),
		"posting_date": filters.from_date,
		"posting_time": "00:00:00"
	})
	row = [""]*len(columns)
	row[1] = _("'Opening'")
	for i, v in ((9, 'qty_after_transaction'), (11, 'valuation_rate'), (12, 'stock_value')):
			row[i] = last_entry.get(v, 0)

	return row

def get_warehouse_condition(warehouse):
	warehouse_details = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt"], as_dict=1)
	if warehouse_details:
		return " exists (select name from `tabWarehouse` wh \
			where wh.lft >= %s and wh.rgt <= %s and warehouse = wh.name)"%(warehouse_details.lft,
			warehouse_details.rgt)

	return ''

def get_item_group_condition(item_group):
	item_group_details = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"], as_dict=1)
	if item_group_details:
		return "item.item_group in (select ig.name from `tabItem Group` ig \
			where ig.lft >= %s and ig.rgt <= %s and item.item_group = ig.name)"%(item_group_details.lft,
			item_group_details.rgt)

	return ''
