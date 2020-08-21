/*
frappe.form.link_formatters['Employee'] = function(value, doc) {
    if(doc.employee_name && doc.employee_name !== value) {
        return value + ': ' + doc.employee_name;
    } else {
        return value;
    }
}

frappe.form.link_formatters['Item'] = function(value, doc) {
    if (doc.doctype != "Batch"){
    if(doc.item_name && doc.item_name !== value) {
        return value + ': ' + doc.item_name;
    } else {
        return value;
    }
    }
}
*/

frappe.Application.prototype.show_update_available = function () {
	frappe.show_alert({"message":"Welcome back to VEF Solution Indonesia"},3);
	//frappe.hide_msgprint();
	if (frappe.user_roles.includes('Administrator')){
		frappe.call({
			"method": "frappe.utils.change_log.show_update_popup"
		});
	}
}
erpnext.show_serial_batch_selector = function(frm, d, callback, on_close, show_dialog) {
	frappe.require("assets/custom1/js/serial_no_batch_selector.js", function() {
		new erpnext.SerialNoBatchSelector({
			frm: frm,
			item: d,
			warehouse_details: {
				type: "Warehouse",
				name: d.warehouse
			},
			callback: callback,
			on_close: on_close
		}, show_dialog);
	});
}