
frappe.provide('frappe.views');

frappe.views.ReportView2 = class ReportView2 extends frappe.views.ListView {
	setup_defaults() {
		super.setup_defaults();
		console.log('add custom resport menu...');
		this.page.add_actions_menu_item({
			label: __('HOHO'),
			action: () => {
				frappe.add_to_desktop(
					this.report_name || __('{0} Report', [this.doctype]),
					this.doctype, this.report_name
				);
			}, standard: true}); 
	}
};

const report_menu2 = new frappe.views.ReportView2();
report_menu2.setup_defaults();

//console.log(this.page_title);