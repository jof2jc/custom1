// Copyright (c) 2020, jonathan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Score Card', {
	refresh: function(frm) {
		frm.set_query('academic_term', function(){
			return {
				filters: {
					academic_year: ["=", frm.doc.academic_year]
				}
			};
		});
	},
});
