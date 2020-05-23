// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Sales Invoice'] = {
	add_fields: ["order_status","is_return"],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
		var status_color = {
			"Draft": "red",
			"Unpaid": "orange",
			"Paid": "green",
			"Return": "darkgrey",
			"Credit Note Issued": "darkgrey",
			"Unpaid and Discounted": "orange",
			"Overdue and Discounted": "red",
			"Overdue": "red",
			"To Pack": "orange",
			"To Pick": "orange",
			"To Deliver": "orange",
			"Cancelled": "red",
			"Pending": "darkgrey",
			"Completed": "blue",
			"Stock-Out": "blue",
			"Send to QC": "red"

		};
		if (frappe.meta.has_field("Sales Invoice","order_status")){
			if (status_color[doc.order_status] && doc.docstatus == 0 && doc.is_return == 0){
				return [__(doc.order_status), status_color[doc.order_status]];
			} else {
				return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
			}
		}
		else {
			return [__(doc.status), status_color[doc.status], "status,=,"+doc.status];
		}
	},
	right_column: "grand_total"
};
