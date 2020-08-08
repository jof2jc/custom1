from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time, get_site_name

from frappe.utils.dateutils import parse_date
import json
import datetime
import erpnext.accounts.utils
from re import sub


@frappe.whitelist()
def get_customer_part_no(doctype, txt, searchfield, start, page_len, filters):
	query = """select ref_code, ref_name from `tabItem Customer Detail`
		where ref_code like '{txt}'""".format(txt = frappe.db.escape('%{0}%'.format(txt)))

	if filters and filters.get('item_code'):
		query += " and parent = '{item_code}'".format(item_code = frappe.db.escape(filters.get('item_code')))

	return frappe.db.sql(query)