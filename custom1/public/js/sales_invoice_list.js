// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

// render
frappe.listview_settings['Sales Invoice'] = {
	add_fields: ["customer", "status", "base_grand_total", "outstanding_amount", "due_date", "company",
		"currency", "is_return"],
	get_indicator: function(doc) {
		if (doc.company == "DCENDOL SERPONG"){
		if(flt(doc.outstanding_amount)==0) {
			return [__("Open"), "green", "outstanding_amount,=,0"]
		} else if(flt(doc.outstanding_amount) < 0) {
			return [__("Credit Note Issued"), "darkgrey", "outstanding_amount,<,0"]
		} else if (flt(doc.outstanding_amount) > 0 && doc.due_date >= frappe.datetime.get_today()) {
			return [__("Unpaid"), "orange", "outstanding_amount,>,0|due_date,>,Today"]
		} else if (flt(doc.outstanding_amount) > 0 && doc.due_date < frappe.datetime.get_today()) {
			return [__("Overdue"), "red", "outstanding_amount,>,0|due_date,<=,Today"]
		}
		//if (doc.status == "Draft"){
			return [__("Ongoing"), "orange"]
		//}
		}
		//console.log(doc.docstatus);
	},
	right_column: "grand_total"
};
