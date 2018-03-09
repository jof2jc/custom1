frappe.pages['welcome-to-erpnext'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Welcome to ERPNext',
		single_column: true
	});
}