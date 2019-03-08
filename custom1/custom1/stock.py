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

@frappe.whitelist()
def get_price_list_rate(item_code, price_list=None):
	if not price_list:
		price_list = frappe.db.get_single_value('Selling Settings', 'selling_price_list')

	res = [{ "harga": 0.0 }]
	

	res[0]["harga"] = frappe.db.get_value("Item Price",
			{"price_list": price_list, "item_code": item_code}, "price_list_rate")
	return res

@frappe.whitelist()
def get_latest_stock_qty(item_code, warehouse=None):
	values, condition = [item_code], ""
	if warehouse:
		lft, rgt, is_group = frappe.db.get_value("Warehouse", warehouse, ["lft", "rgt", "is_group"])
	
		if is_group:
			values.extend([lft, rgt])
			condition += "and exists (\
				select name from `tabWarehouse` wh where wh.name = tabBin.warehouse\
				and wh.lft >= %s and wh.rgt <= %s)"
	
		else:
			values.append(warehouse)
			condition += " AND warehouse = %s"
	
	actual_qty = frappe.db.sql("""select sum(actual_qty) from tabBin
		where item_code=%s {0}""".format(condition), values)[0][0]

	return actual_qty