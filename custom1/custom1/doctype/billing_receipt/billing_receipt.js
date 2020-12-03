// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt


frappe.ui.form.on('Billing Receipt', {
	onload: function(frm) {
		if(frm.doc.__islocal) {
			frm.set_value("from_date",frappe.datetime.month_start(frm.doc.posting_date));
			frm.set_value("to_date",frappe.datetime.month_end(frm.doc.posting_date));
			frm.events.payment_type(frm);
		}
	},
	
	setup: function(frm) {

		frm.set_query("party_type", function() {
			return{
				"filters": {
					"name": ["in",["Customer","Supplier"]],
				}
			}
		});

		frm.set_query("reference_doctype", "references", function() {
			if (frm.doc.party_type=="Customer") {
				var doctypes = ["Sales Order", "Sales Invoice", "Journal Entry"];
			} else if (frm.doc.party_type=="Supplier") {
				var doctypes = ["Purchase Order", "Purchase Invoice", "Journal Entry"];
			}

			return {
				filters: { "name": ["in", doctypes] }
			};
		});

		frm.set_query("reference_name", "references", function(doc, cdt, cdn) {
			child = locals[cdt][cdn];
			filters = {"docstatus": 1, "company": doc.company};
			party_type_doctypes = ['Sales Invoice', 'Sales Order', 'Purchase Invoice', 
				'Purchase Order'];

			if (in_list(party_type_doctypes, child.reference_doctype)) {
				filters[doc.party_type.toLowerCase()] = doc.party;
			}

			return {
				filters: filters
			};
		});
	},

	refresh: function(frm) {
		if(frm.doc.docstatus != 1){
			$( ".fa.fa-print" ).hide();
			//frm.print_icon.addClass("hide");
			frm.page.hide_menu();
		}
	},

	from_date: function(frm) {
		frm.events.get_outstanding_documents(frm)
	},
	to_date: function(frm) {
		frm.events.get_outstanding_documents(frm)
	},
	show_all: function(frm) {
		frm.events.get_outstanding_documents(frm)
	},
	payment_type: function(frm) {
		if(frm.doc.party) {
			frm.events.party(frm);	
		}
		frm.set_value("party_type",frm.doc.payment_type == "Receive" ? "Customer" : "Supplier");
		
	},

	party_type: function(frm) {
		if(frm.doc.party) {
			$.each(["party", "references"],
				function(i, field) {
					frm.set_value(field, null);
				})
		}
		
	},

	party: function(frm) {
		if(frm.doc.payment_type && frm.doc.party_type && frm.doc.party) {
			if(!frm.doc.posting_date) {
				frappe.msgprint(__("Please select Posting Date before selecting Party"))
				frm.set_value("party", "");
				return ;
			}

			return frappe.call({
				method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_party_details",
				args: {
					company: frm.doc.company,
					party_type: frm.doc.party_type,
					party: frm.doc.party,
					date: frm.doc.posting_date
				},
				callback: function(r, rt) {
					if(r.message) {
						frappe.run_serially([
							() => frm.set_value("party_name", r.message.party_name),
							() => frm.events.get_outstanding_documents(frm)
						]);
					}
				}
			});
		}
	},

	get_outstanding_documents: function(frm) {
		frm.clear_table("references");

		if(!frm.doc.party) return;

		frm.events.check_mandatory_to_fetch(frm);
		var company_currency = frappe.get_doc(":Company", frm.doc.company).default_currency;

		console.log('fetching outstanding documents..');
		return  frappe.call({
			method: 'custom1.custom1.custom1.get_outstanding_reference_documents2',
			args: {
				args: {
					"posting_date": frm.doc.posting_date,
					"company": frm.doc.company,
					"party_type": frm.doc.party_type,
					"payment_type": frm.doc.payment_type,
					"party": frm.doc.party,
					"party_account": "",
					"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date,
					"show_all": frm.doc.show_all,
					"is_billing_receipt": 1
				}
			},
			callback: function(r, rt) {
				console.log('r.message === ' + r.message);
				if(r.message) {
					var total_positive_outstanding = 0;
					var total_negative_outstanding = 0;
					var total_amount = 0;

					$.each(r.message, function(i, d) {
						var c = frm.add_child("references");
						c.reference_doctype = d.voucher_type;
						c.reference_name = d.voucher_no;
						c.posting_date = d.posting_date;
						c.due_date = d.due_date
						c.total_amount = d.invoice_amount;
						c.outstanding_amount = d.outstanding_amount;
						c.bill_no = d.bill_no;

						if(flt(d.outstanding_amount) > 0)
							total_amount += flt(d.outstanding_amount);

						if (in_list(['Sales Invoice', 'Purchase Invoice', "Expense Claim", "Fees"], d.reference_doctype)){
							c.due_date = d.due_date;
						}
					});
					frm.set_value("total_amount",total_amount);
					frm.refresh_fields();
				} else {
					frm.clear_table("references");
					frm.refresh_fields();
				}
			}
		});
	},

	check_mandatory_to_fetch: function(frm) {
		$.each(["Company", "Party Type", "Party", "payment_type","from_date","to_date"], function(i, field) {
			if(!frm.doc[frappe.model.scrub(field)]) {
				frappe.msgprint(__("Please select {0} first", [field]));
				return false;
			}

		});
	},
	set_total_amount: function(frm) {
		var total_outstanding_amount = 0.0;

		$.each(frm.doc.references || [], function(i, row) {
			if (row.outstanding_amount) {
				total_outstanding_amount += flt(row.outstanding_amount);
			}
		});
		frm.set_value("total_amount", Math.abs(total_outstanding_amount));
	},

	validate: function(frm){
		console.log('validate...');
		frm.events.set_total_amount(frm);
	},

	validate_row: function(frm, row) {
		var _validate = function(i, row) {
			if (!row.reference_doctype) {
				return;
			}

			if(frm.doc.party_type=="Customer" &&
				!in_list(["Sales Order", "Sales Invoice", "Journal Entry"], row.reference_doctype)
			) {
				frappe.model.set_value(row.doctype, row.name, "reference_doctype", null);
				frappe.msgprint(__("Row #{0}: Reference Document Type must be one of Sales Order, Sales Invoice or Journal Entry", [row.idx]));
				return false;
			}

			if(frm.doc.party_type=="Supplier" &&
				!in_list(["Purchase Order", "Purchase Invoice", "Journal Entry"], row.reference_doctype)
			) {
				frappe.model.set_value(row.doctype, row.name, "against_voucher_type", null);
				frappe.msgprint(__("Row #{0}: Reference Document Type must be one of Purchase Order, Purchase Invoice or Journal Entry", [row.idx]));
				return false;
			}
			
		}

	}
});


frappe.ui.form.on('Billing Receipt Reference', {
	reference_doctype: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frm.events.validate_row(frm, row);
	},

	reference_name: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.reference_name && row.reference_doctype) {
			return frappe.call({
				method: "custom1.custom1.pbs.get_reference_details",
				args: {
					reference_doctype: row.reference_doctype,
					reference_name: row.reference_name,
					party_account_currency: frappe.get_doc(":Company", frm.doc.company).default_currency
				},
				callback: function(r, rt) {
					if(r.message) {
						$.each(r.message, function(field, value) {
							frappe.model.set_value(cdt, cdn, field, value);
							//c.posting_date = d.posting_date;
						})
						frm.events.set_total_amount(frm);
						frm.refresh_fields();
					}
					
				}
			})
		}
	},

	references_remove: function(frm) {
		frm.events.set_total_amount(frm);
	}
})
