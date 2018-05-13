# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.utils import flt

def execute(filters=None):
	if not filters: filters = {}

	columns = get_columns(filters)
	awb_map = get_awb_details(filters)
	
	data = []

	for awb in sorted(awb_map):
		data.append([awb.name, awb.bill_date, awb.awb_no, awb.courier, awb.invoice_no, awb.customer, awb.shipping_fee, awb.actual_shipping_fee, 
				(awb.shipping_fee - awb.actual_shipping_fee), flt(awb.actual_weight)
			])

	return columns, data


def get_columns(filters):
	"""return columns based on filters"""

	columns = [_("ID") + ":Link/Online Shipping Log:75", _("Date") + ":Date:100", _("AWB No / Resi") + "::150",_("Courier") + "::85", 
			_("Invoice / Order No") + ":Link/Sales Invoice:165", 
			_("Customer") + ":Link/Customer:125",
			_("Shipping Fee") + ":Float:100",  _("Actual Shipping Fee") + ":Float:100",
			_("Difference") + ":Float:100", _("Actual Weight") + ":Float:80"]
	return columns

def get_conditions(filters):
	conditions = ""

	#if filters.get("customer"): conditions += " and si.customer = %(customer)s"

	if filters.get("from_date"): conditions += " and sl.bill_date >= %(from_date)s"
	if filters.get("to_date"): conditions += " and sl.bill_date <= %(to_date)s"

	return conditions

def get_awb_details(filters):
	"""returns all items details"""

	conditions = get_conditions(filters)

	awb_map = frappe.db.sql("""select sl.name, sl.bill_date, sl.awb_no, sl.courier, sl.invoice_no, si.customer, ifnull(si.shipping_fee,0) as shipping_fee, 
				ifnull(sl.actual_shipping_fee,0) as actual_shipping_fee, sl.actual_weight from `tabOnline Shipping Log` sl left join 
			`tabSales Invoice` si on sl.awb_no=si.awb_no where sl.actual_shipping_fee > 0 and sl.docstatus=1 and sl.latest=1 %s""" % conditions, filters, as_dict=1)

	return awb_map

