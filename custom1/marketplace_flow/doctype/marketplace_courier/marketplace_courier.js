// Copyright (c) 2020, jonathan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Marketplace Courier', {
	refresh: function(frm) {
		frm.set_query("shipping_account", function() {
			return {
				"filters": {
					"root_type": "Expense",
					"account_type": "Expense Account",
					"disabled": 0,
					"is_group": 0,
					"freeze_account": "No"
				}
			};
		});
	}
});
