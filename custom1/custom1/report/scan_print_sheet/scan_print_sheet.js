// Copyright (c) 2016, jonathan and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Scan Print Sheet"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("company"),
			"reqd": 1
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname":"territory",
			"label": __("Territory"),
			"fieldtype": "Link",
			"options": "Territory",
			"reqd": 0
		},
		{
			"fieldname":"cancelled",
			"label": __("Include Cancelled?"),
			"fieldtype": "Check",
			"default": 0,
			"reqd": 0
		}
	]
}
