// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

function random4Digit(){
  return shuffle( "0123456789".split('') ).join('').substring(0,4);
}

function shuffle(o){
    for(var j, x, i = o.length; i; j = Math.floor(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
    return o;
}

var footnote;//alert(new Date(frappe.datetime.add_months(frappe.datetime.get_today(), -1)));

frappe.db.get_value("Terms and Conditions", {"name":"Tanda Terima"}, ["terms"], function(v) {
if (v) footnote = v.terms
else footnote = random4Digit();

frappe.query_reports["Tanda Terima"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"customer",
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname":"mode_of_payment",
			"label": __("Mode of Payment"),
			"fieldtype": "Link",
			"options": "Mode of Payment"
		},
		{
			"fieldname":"footnote",
			"label": __("Foot Notes"),
			"fieldtype": "Small Text",
			"default": footnote
		}
	]
}
});