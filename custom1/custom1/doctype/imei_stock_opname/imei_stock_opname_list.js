frappe.listview_settings['IMEI Stock Opname'] = {
	add_fields: ["status"],
	get_indicator: function (doc) {
		return [__(doc.status), {
			"Pending": "red",
			"Completed": "green"
		}[doc.status], "status,=," + doc.status];
	}

};