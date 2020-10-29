# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt,cstr, nowdate, date_diff, getdate, format_datetime, format_time, formatdate, get_datetime, get_time, get_weekday

def execute(filters=None):
	if not filters: filters = {}
	data_map = {}
	columns = []
	columns = get_columns(filters)
	data = []

	data_map = get_data(filters)
	
	for d in data_map:
		data.append([d.name, d.type, d.transaction_ref_no, 
				getdate(get_datetime(d.time_start)), get_time(get_datetime(d.time_start)).strftime("%H:%M:%S"), d.weekday_start or get_weekday(get_datetime(d.time_start)),
				getdate(get_datetime(d.time_end)), get_time(get_datetime(d.time_end)).strftime("%H:%M:%S"), d.weekday_end or get_weekday(get_datetime(d.time_end)),
				d.score
			])

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	columns = [_("ID") + ":Link/Marketplace Fulfillment Score Card:120", _("Type") + ":Data:150", _("Transaction Ref No") + ":Link/Sales Invoice:150", 
			_("Date Start") + ":Date:100", _("Time Start") + ":Time:100", _("Weekday Start") + ":Data:100",
			_("Date End") + ":Date:100", _("Time End") + ":Time:100", _("Weekday End") + ":Data:100",
			_("Score Label") + ":Data:150"
		]

	return columns

def get_conditions(filters):
	conditions = []

	if filters.get("from_date"):
		conditions.append("date(time_start) between %(from_date)s and %(to_date)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_data(filters):
	"""returns all data details"""

	data_map = {}
	data_map = frappe.db.sql("""select name, type, transaction_ref_no, time_start, time_end, weekday_start, weekday_end, score
			from `tabMarketplace Fulfillment Score Card`
			where ifnull(name,'') <> '' {conditions} order by time_start desc"""\
			.format(conditions=get_conditions(filters)), filters, as_dict=1)
	#print data_map
	return data_map

def get_pl_conditions(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("ip.item_code=%(item_code)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""



