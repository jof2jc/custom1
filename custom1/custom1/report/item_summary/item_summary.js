// Copyright (c) 2016, jonathan and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item Summary"] = {
	"filters": [
			{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			//"default": frappe.defaults.get_user_default("company"),
			"reqd": 0
			},
			{
			"fieldname":"item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
			}
	]
}
