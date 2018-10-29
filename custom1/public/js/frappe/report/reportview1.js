// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.
frappe.provide('frappe.views.report_view');

frappe.views.ReportView.prototype.make_export = function(doc){
		var me = this;
		if(!frappe.model.can_export(this.doctype)) {
			return;
		}
		var export_btn = this.page.add_menu_item(__('Export'), function() {
			var args = me.get_args();
			var selected_items = me.get_checked_items()
			frappe.prompt({fieldtype:"Select", label: __("Select File Type"), fieldname:"file_format_type",
				options:"Excel\nCSV", default:"Excel", reqd: 1},
				function(data) {
					args.cmd = 'frappe.desk.reportview.export_query';
					args.file_format_type = data.file_format_type;

					if(me.add_totals_row) {
						args.add_totals_row = 1;
					}

					if(selected_items.length >= 1) {
						args.selected_items = $.map(selected_items, function(d) { return d.name; });
					}
					open_url_post(frappe.request.url, args);

				}, __("Export: {0}",[__(me.doctype)]), __("Download"));

		}, true); 
		if (this.docname == "eFaktur"){
			var export_btn = this.page.add_menu_item(__('Export eFaktur'), function() {
			var args = me.get_args();
			var selected_items = me.get_checked_items()
			frappe.prompt([{fieldtype:"Select", label: __("Select File Type"), fieldname:"file_format_type",
				options:"Excel\nCSV", default:"CSV", reqd: 1},
				{fieldtype:"Data", label: __("Last eFaktur No"), fieldname:"last_efaktur_no",default:"0000000000000",reqd: 1}],
				function(data) {
					args.cmd = 'custom1.desk1.reportview.export_query';
					args.file_format_type = data.file_format_type;
					args.last_efaktur_no = data.last_efaktur_no;

					if(me.add_totals_row) {
						args.add_totals_row = 1;
					}

					if(selected_items.length >= 1) {
						args.selected_items = $.map(selected_items, function(d) { return d.name; });
					}
					open_url_post(frappe.request.url, args);

				}, __("Export Efaktur: {0}",[__(me.doctype)]), __("Download"));

			}, false);
		}
	
}

