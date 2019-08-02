// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide('erpnext');

// add toolbar icon
$(document).bind('toolbar_setup', function() {
	frappe.app.name = "ERPNext";

	$('.navbar-home').html('Home');

});



// doctypes created via tree
$.extend(frappe.create_routes, {
	"Customer Group": "Tree/Customer Group",
	"Territory": "Tree/Territory",
	"Item Group": "Tree/Item Group",
	"Sales Person": "Tree/Sales Person",
	"Account": "Tree/Account",
	"Cost Center": "Tree/Cost Center",
	"Department": "Tree/Department",
});

// preferred modules for breadcrumbs
$.extend(frappe.breadcrumbs.preferred, {
	"Item Group": "Stock",
	"Customer Group": "Selling",
	"Supplier Group": "Buying",
	"Territory": "Selling",
	"Sales Person": "Selling",
	"Sales Partner": "Selling",
	"Brand": "Selling"
});
