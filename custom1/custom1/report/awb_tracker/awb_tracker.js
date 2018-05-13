// Copyright (c) 2016, jonathan and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["AWB Tracker"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_days(frappe.datetime.get_today(), -7),
			"width": "80"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		}
	],
	"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
    		value = default_formatter(row, cell, value, columnDef, dataContext);
			if (dataContext.Difference < 0 && (columnDef.id == "Difference" || columnDef.id == "AWB No / Resi") ) {
				//var $value = $(value).css("font-weight", "bold");
				//value = $value.wrap("<p></p>").parent().html();
				 value = "<span style='color:#CB4335;'>" + value + "</span>";
                                    
			}
			else value = "<span style='font-weight:normal;'>" + value + "</span>";
		return value;
	}

}
