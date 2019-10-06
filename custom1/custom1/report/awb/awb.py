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
		data.append([d.name, 1, d.qty, d.docstatus, d.order_status, d.customer, d.courier, d.awb_no,
				d.posting_date, d.creation, d.delivery_date, date_diff(d.delivery_date or nowdate(),d.creation)	
			])

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	columns = [_("Order ID") + ":Link/Sales Invoice:150", _("Pack") + ":Int:50", _("Qty") + ":Float:50", _("Status") + "::60", _("Order Status") + "::100", _("Store Name") + ":Link/Customer:120", 
			_("Courier") + "::100", _("AWB No") + "::120", _("Order Date") + ":Date:80",_("Upload Date") + ":Date:80", 
			_("Delivery Date") + ":Date:80", _("Days") + ":Int:50"
		]

	return columns

def get_conditions(filters):
	conditions = []

	if filters.get("company"):
		conditions.append("si.company=%(company)s")

	if filters.get("from_date"):
		conditions.append("date(si.creation) between %(from_date)s and %(to_date)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""

def get_data(filters):
	"""returns all data details"""

	data_map = {}
	#frappe.msgprint("""select name,customer, awb_no, status, order_status, posting_date, creation, delivery_date, courier 
	#		from `tabSales Invoice` where is_return=0 {conditions}""".format(conditions=get_conditions(filters)))

	data_map = frappe.db.sql("""select si.name, sum(si_item.qty) as qty, si.customer, si.awb_no, si.docstatus, si.order_status, si.posting_date, 
				date(si.creation) as creation, si.delivery_date, si.courier 
			from `tabSales Invoice` si join `tabSales Invoice Item` si_item on si.name=si_item.parent 
			where si.docstatus <=1 and si.is_return=0 {conditions} 
			group by si.name, si.customer, si.awb_no, si.docstatus, si.order_status, si.posting_date, si.delivery_date, si.courier
			order by date(si.creation) desc"""\
			.format(conditions=get_conditions(filters)), filters, as_dict=1)
	#print data_map
	return data_map

def get_pl_conditions(filters):
	conditions = []
	if filters.get("item_code"):
		conditions.append("ip.item_code=%(item_code)s")

	return "and {}".format(" and ".join(conditions)) if conditions else ""



