import VEFBulkOperations from "./bulk_operation";

frappe.provide('frappe.views');

frappe.views.ListView.prototype.get_actions_menu_items = function () {
		const doctype = this.doctype;
		const actions_menu_items = [];
		const bulk_operations = new VEFBulkOperations({ doctype: this.doctype });

		const is_field_editable = (field_doc) => {
			return field_doc.fieldname && frappe.model.is_value_type(field_doc)
				&& field_doc.fieldtype !== 'Read Only' && !field_doc.hidden && !field_doc.read_only;
		};

		const has_editable_fields = (doctype) => {
			return frappe.meta.get_docfields(doctype).some(field_doc => is_field_editable(field_doc));
		};

		const has_submit_permission = (doctype) => {
			return frappe.perm.has_perm(doctype, 0, 'submit');
		};

		// utility
		const bulk_assignment = () => {
			return {
				label: __('Assign To'),
				action: () => bulk_operations.assign(this.get_checked_items(true), this.refresh),
				standard: true
			};
		};

		const bulk_assignment_rule = () => {
			return {
				label: __('Apply Assignment Rule'),
				action: () => bulk_operations.apply_assignment_rule(this.get_checked_items(true), this.refresh),
				standard: true
			};
		};

		const bulk_printing = () => {
			return {
				label: __('Print'),
				action: () => bulk_operations.print(this.get_checked_items()),
				standard: true
			};
		};

		const bulk_delete = () => {
			return {
				label: __('Delete'),
				action: () => {
					const docnames = this.get_checked_items(true).map(docname => docname.toString());
					frappe.confirm(__('Delete {0} items permanently?', [docnames.length]),
						() => bulk_operations.delete(docnames, this.refresh));
				},
				standard: true,
			};
		};

		const bulk_cancel = () => {
			return {
				label: __('Cancel'),
				action: () => {
					const docnames = this.get_checked_items(true);
					if (docnames.length > 0) {
						frappe.confirm(__('Cancel {0} documents?', [docnames.length]),
							() => bulk_operations.submit_or_cancel(docnames, 'cancel', this.refresh));
					}
				},
				standard: true
			};
		};

		const bulk_submit = () => {
			return {
				label: __('Submit'),
				action: () => {
					const docnames = this.get_checked_items(true);
					if (docnames.length > 0) {
						frappe.confirm(__('Submit {0} documents?', [docnames.length]),
							() => bulk_operations.submit_or_cancel(docnames, 'submit', this.refresh));
					}
				},
				standard: true
			};
		};

		const bulk_edit = () => {
			return {
				label: __('Edit'),
				action: () => {
					let field_mappings = {};

					frappe.meta.get_docfields(doctype).forEach(field_doc => {
						if (is_field_editable(field_doc)) {
							field_mappings[field_doc.label] = Object.assign({}, field_doc);
						}
					});

					const docnames = this.get_checked_items(true);

					bulk_operations.edit(docnames, field_mappings, this.refresh);
				},
				standard: true
			};
		};

		// bulk edit
		if (has_editable_fields(doctype)) {
			actions_menu_items.push(bulk_edit());
		}

		// bulk assignment
		actions_menu_items.push(bulk_assignment());

		actions_menu_items.push(bulk_assignment_rule());

		// bulk printing
		if (frappe.model.can_print(doctype)) {
			actions_menu_items.push(bulk_printing());
		}

		// bulk submit
		if (frappe.model.is_submittable(doctype) && has_submit_permission(doctype) && !(frappe.model.has_workflow(doctype))) {
			actions_menu_items.push(bulk_submit());
		}

		// bulk cancel
		if (frappe.model.can_cancel(doctype) && !(frappe.model.has_workflow(doctype))) {
			actions_menu_items.push(bulk_cancel());
		}

		// bulk delete
		if (frappe.model.can_delete(doctype)) {
			actions_menu_items.push(bulk_delete());
		}

		return actions_menu_items;
	
}