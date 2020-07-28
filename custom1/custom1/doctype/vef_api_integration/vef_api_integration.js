// Copyright (c) 2020, jonathan and contributors
// For license information, please see license.txt



frappe.ui.form.on("VEF API Integration", "try", function(frm, cdt, cdn) { 
	return frm.call({
		doc: frm.doc,
		method: "test_api_request",
		callback: function(r) {
			//if(!r.exc) 
		}
	});
});

frappe.ui.form.on("VEF API Integration", "generate_access_token", function(frm, cdt, cdn) { 
	frappe.call({
		method: "custom1.custom1.doctype.vef_api_integration.vef_api_integration.generate_access_token", 
		args: {
			"docname": frm.doc.name
		},
		callback: function(r) {
			console.log("access_token === " + r.message);
			if (r.message){
				frm.set_value("access_token",r.message)
			}
		}
	});
});
frappe.ui.form.on("VEF API Integration", "generate_signature", function(frm, cdt, cdn) { 
	frappe.call({
		method: "custom1.custom1.doctype.vef_api_integration.vef_api_integration.generate_signature", 
		args: {
			"docname": frm.doc.name,
			"url_path": frm.doc.url,
			"method": frm.doc.method,
			"access_token": frm.doc.access_token,
			"BodyString": frm.doc.body || '',
			"timestamp": frm.doc.timestamp || ''
		},
		callback: function(r) {
			console.log("signature === " + r.message);
			if (r.message){
				frm.set_value("signature",r.message)
			}
		}
	});
});