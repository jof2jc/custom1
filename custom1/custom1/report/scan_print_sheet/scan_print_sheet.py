# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt,cstr, nowdate, date_diff, getdate

def execute(filters=None):
	if not filters: filters = {}
	data_map = {}
	columns = []
	columns = get_columns(filters)
	data = []

	data_map = get_data(filters)
	
	for d in data_map:
		data.append([d.name, d.marketplace_courier, d.sales_team, d.pack or 1.0, d.printed, d.transaction_date, d.delivered, d.delivery_date,
				d.territory, d.cancelled, d.company, d.scan_print_ref, d.scan_out_ref
			])

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	columns = [_("AWB No") + ":Link/AWB Invoice:150", _("Courier") + ":Link/Marketplace Courier:120", _("Sales Team") + ":Link/Sales Person:100", 
			_("Pack") + ":Float:50", _("Printed") + ":Int:80", 
			_("Date") + ":Datetime:120", _("Delivered") + ":Int:80", 
			_("Delivery Date") + ":Datetime:120", _("Territory") + ":Link/Territory:100", _("Cancelled") + "::80",
			_("Company") + ":Link/Company:100", _("Scan Print Ref") + ":Link/Scan Print:120",
			_("Scan Out Ref") + ":Link/Scan Print:120"
		]

	return columns

def get_conditions(filters):
	conditions = []

	if filters.get("company"):
		conditions.append("si.company=%(company)s")

	if not filters.get("cancelled"):
		conditions.append("si.cancelled <> 1")

	if filters.get("from_date"):
		conditions.append("date(si.transaction_date) between %(from_date)s and %(to_date)s")

	if filters.get("territory"):
		conditions.append("si.territory=%(territory)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_data(filters):
	"""returns all data details"""

	data_map = {}
	data_map = frappe.db.sql("""select name, marketplace_courier, sales_team, pack, printed, transaction_date, delivered, delivery_date, territory, cancelled, scan_print_ref, scan_out_ref, company 
			from `tabAWB Invoice` si
			where printed=1 {conditions} order by si.transaction_date desc"""\
			.format(conditions=get_conditions(filters)), filters, as_dict=1)
	#print data_map
	return data_map

def get_pl_conditions(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("ip.item_code=%(item_code)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""



