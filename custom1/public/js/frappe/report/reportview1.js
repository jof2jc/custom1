
frappe.provide('frappe.views');

frappe.views.ReportView.prototype.report_menu_items = function(doc){
		const route = frappe.get_route();
		if (route.length === 4) {
			this.report_name = route[3];
		}


		let items = [
			{
				label: __('Show Totals'),
				action: () => {
					this.add_totals_row = !this.add_totals_row;
					this.save_view_user_settings(
						{ add_totals_row: this.add_totals_row });
					this.datatable.refresh(this.get_data(this.data));
				}
			},
			{
				label: __('Print'),
				action: () => {
					// prepare rows in their current state, sorted and filtered
					const rows_in_order = this.datatable.datamanager.rowViewOrder.map(index => {
						if (this.datatable.bodyRenderer.visibleRowIndices.includes(index)) {
							return this.data[index];
						}
					}).filter(Boolean);

					if (this.add_totals_row) {
						const total_data = this.get_columns_totals(this.data);

						total_data['name'] = __('Totals').bold();
						rows_in_order.push(total_data);
					}

					frappe.ui.get_print_settings(false, (print_settings) => {
						var title =  this.report_name || __(this.doctype);
						frappe.render_grid({
							title: title,
							subtitle: this.get_filters_html_for_print(),
							print_settings: print_settings,
							columns: this.columns,
							data: rows_in_order
						});
					});
				}
			},
			{
				label: __('Toggle Chart'),
				action: () => this.toggle_charts()
			},
			{
				label: __('Toggle Sidebar'),
				action: () => this.toggle_side_bar(),
				shortcut: 'Ctrl+K',
			},
			{
				label: __('Pick Columns'),
				action: () => {
					const d = new frappe.ui.Dialog({
						title: __('Pick Columns'),
						fields: this.get_dialog_fields(),
						primary_action: (values) => {
							// doctype fields
							let fields = values[this.doctype].map(f => [f, this.doctype]);
							delete values[this.doctype];

							// child table fields
							for (let cdt in values) {
								fields = fields.concat(values[cdt].map(f => [f, cdt]));
							}

							// always keep name (ID) column
							this.fields = [["name", this.doctype], ...fields];

							this.fields.map(f => this.add_currency_column(f[0], f[1]));

							this.build_fields();
							this.setup_columns();

							this.datatable.destroy();
							this.datatable = null;
							this.refresh();

							d.hide();
						}
					});

					d.show();
				}
			}
		];
		
		//export efaktur
		if (this.report_name == "eFaktur") {
			items.push({
				label: __('Export eFaktur'),
				action: () => {
					const args = this.get_args();
					const selected_items = this.get_checked_items(true);
					let fields = [
						{
							fieldtype: 'Select',
							label: __('Select File Type'),
							fieldname:'file_format_type',
							options: ['Excel', 'CSV'],
							default: 'CSV'
						},
						{
							fieldtype:"Data", 
							label: __("Last eFaktur No"), 
							fieldname:"last_efaktur_no",
							default:"0000000000000",
							reqd: 1
						}
					];

					if (this.total_count > args.page_length) {
						fields.push({
							fieldtype: 'Check',
							fieldname: 'export_all_rows',
							label: __('Export All {0} rows?', [(this.total_count + "").bold()])
						});
					}

					const d = new frappe.ui.Dialog({
						title: __("Export Report: {0}",[__(this.doctype)]),
						fields: fields,
						primary_action_label: __('Download'),
						primary_action: (data) => {
							args.cmd = 'custom1.desk1.reportview.export_query';
							args.file_format_type = data.file_format_type;
							args.last_efaktur_no = data.last_efaktur_no;
							args.title = this.report_name || this.doctype;

							console.log(args.last_efaktur_no);

							if(this.add_totals_row) {
								args.add_totals_row = 1;
							}

							if(selected_items.length > 0) {
								args.selected_items = selected_items;
							}

							if (!data.export_all_rows) {
								args.start = 0;
								args.page_length = this.data.length;
							} else {
								delete args.start;
								delete args.page_length;
							}

							open_url_post(frappe.request.url, args);

							d.hide();
						},
					});

					d.show();
				}
			});
		}

		if (frappe.model.can_export(this.doctype)) {
			items.push({
				label: __('Export'),
				action: () => {
					const args = this.get_args();
					const selected_items = this.get_checked_items(true);
					let fields = [
						{
							fieldtype: 'Select',
							label: __('Select File Type'),
							fieldname:'file_format_type',
							options: ['Excel', 'CSV'],
							default: 'Excel'
						}
					];

					if (this.total_count > args.page_length) {
						fields.push({
							fieldtype: 'Check',
							fieldname: 'export_all_rows',
							label: __('Export All {0} rows?', [(this.total_count + "").bold()])
						});
					}

					const d = new frappe.ui.Dialog({
						title: __("Export Report: {0}",[__(this.doctype)]),
						fields: fields,
						primary_action_label: __('Download'),
						primary_action: (data) => {
							args.cmd = 'frappe.desk.reportview.export_query';
							args.file_format_type = data.file_format_type;
							args.title = this.report_name || this.doctype;

							if(this.add_totals_row) {
								args.add_totals_row = 1;
							}

							if(selected_items.length > 0) {
								args.selected_items = selected_items;
							}

							if (!data.export_all_rows) {
								args.start = 0;
								args.page_length = this.data.length;
							} else {
								delete args.start;
								delete args.page_length;
							}

							open_url_post(frappe.request.url, args);

							d.hide();
						},
					});

					d.show();
				}
			});
		}

		items.push({
			label: __("Setup Auto Email"),
			action: () => {
				if(this.report_name) {
					frappe.set_route('List', 'Auto Email Report', {'report' : this.report_name});
				} else {
					frappe.msgprint(__('Please save the report first'));
				}
			}
		});

		// save buttons
		if(frappe.user.is_report_manager()) {
			items = items.concat([
				{ label: __('Save'), action: () => this.save_report('save') },
				{ label: __('Save As'), action: () => this.save_report('save_as') }
			]);
		}

		// user permissions
		if(this.report_name && frappe.model.can_set_user_permissions("Report")) {
			items.push({
				label: __("User Permissions"),
				action: () => {
					const args = {
						doctype: "Report",
						name: this.report_name
					};
					frappe.set_route('List', 'User Permission', args);
				}
			});
		}

		return items.map(i => Object.assign(i, { standard: true }));
	

}