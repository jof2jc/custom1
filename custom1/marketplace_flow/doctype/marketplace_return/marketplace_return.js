// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors // License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.stock");

frappe.ui.form.on('Marketplace Return', {
	setup: function(frm) {

		frm.set_query('batch_no', 'items', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			if(!item.item_code) {
				frappe.throw(__("Please enter Item Code to get Batch Number"));
			} else {
				var filters = {
					'item_code': item.item_code
				}
				

				filters["warehouse"] = item.warehouse || doc.default_warehouse;

				return {
					query : "erpnext.controllers.queries.get_batch_no",
					filters: filters
				}
			}
		});

		frm.set_query('warehouse', 'items', function(doc, cdt, cdn) {
			var item = locals[cdt][cdn];
			return {
				filters: {
					"is_group": 0,
					"disabled": 0
				}
			};

		});

		frm.set_query("default_warehouse", function() {
			return {
				"filters": {
					"company": me.frm.doc.company,
					"is_group": 0
				}
			};
		});

	},
	create_sales_return: function(frm){
		//var me = this.frm;
		if (frm.is_dirty() || frm.doc.docstatus < 1){
			frappe.msgprint({message: 'Please save and approve document first', title: __('Message'), indicator:'blue'}); return;
		}
		this.data = [];
		var dialog = new frappe.ui.Dialog({
			title: __("Create Sales Return (Credit Note) From Customer"),
			fields: [
				{"fieldtype": "Link", "label": __("Customer"), "fieldname": "customer", "options":"Customer",
					"get_query": function () {
						return {
							query:"custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.get_customer",
							filters: {'parent': frm.doc.name}
						}
					}},
					{fieldname: 'items_for_si', fieldtype: 'Table', label: 'Select Items',
					fields: [
						{
							fieldtype:'Data',
							fieldname:'customer',
							label: __('Customer'),
							read_only:1,
							in_list_view:1,
							columns:2
						},
						{
							fieldtype:'Data',
							fieldname:'sales_invoice',
							label: __('ID'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_code',
							label: __('Item'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_name',
							label: __('Item name'),
							read_only:1
						},
						{
							fieldtype:'Float',
							fieldname:'qty',
							label: __('Quantity'),
							read_only: 1,
							in_list_view:1
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'uom',
							label: __('UOM')
						},
						{
							fieldtype:'Small Text',
							read_only:1,
							fieldname:'serial_no',
							label: __('Serial No'),
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'batch_no',
							label: __('Batch No')
						}
					],
					data: this.data,
					get_data: function() {
						return this.data;

					}
				},

				{"fieldtype": "Button", "label": __('Create Sales Return'), "fieldname": "make_sales_return", "cssClass": "btn-primary"},
			]
		});

		dialog.fields_dict.make_sales_return.$input.click(function() {
			var args = dialog.get_values();
			let selected_items = dialog.fields_dict.items_for_si.grid.get_selected_children()
			if(selected_items.length == 0) {
				frappe.throw({message: 'Please select Item from Table', title: __('Message'), indicator:'blue'})
			}
			let selected_items_list = []
			for(let i in selected_items){
				selected_items_list.push(selected_items[i].item_code)
			}
			dialog.hide();
			return frappe.call({
				type: "GET",
				method: "custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.make_sales_return",
				args: {
					"source_name": me.frm.doc.name,
					"for_customer": args.customer,
					"selected_items": selected_items_list
				},
				freeze: true,
				callback: function(r) {
					if(!r.exc) {
						// var args = dialog.get_values();
						if (args.customer){
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
						else{
							
						}
					}
				}
			})
		});
		//dialog.get_field("items_for_si").grid.only_sortable()
		//dialog.get_field("items_for_si").refresh()
		dialog.show();

		dialog.fields_dict.customer.$input.on('input change keyup paste select click', function() {
			console.log('filter customer on_change..');
			var args = dialog.get_values();
			//dialog.fields_dict.items_for_si.df.data='';
			this.data = this.data = dialog.fields_dict.items_for_si.df.data = [];

			frm.doc.items.forEach(function(item) {
				console.log('item.sales_invoice = ' + item.sales_invoice);
				console.log('args.customer= ' + args.customer);
				if (!item.sales_return_no && item.sales_invoice && item.customer == args.customer) 
					dialog.fields_dict.items_for_si.df.data.push(item);
			});
			//if (!args.customer) dialog.fields_dict.items_for_si.df.data = frm.doc.items;

			this.data = dialog.fields_dict.items_for_si.df.data;
			dialog.fields_dict.items_for_si.grid.refresh();
		});
		//dialog.fields_dict.customer.$input.trigger();
		this.data = dialog.fields_dict.items_for_si.df.data;
		dialog.fields_dict.items_for_si.grid.refresh();
	},
	create_purchase_return: function(frm){
		//var me = this.frm;
		if (frm.is_dirty() || frm.doc.docstatus < 1){
			frappe.msgprint({message: 'Please save and approve document first', title: __('Message'), indicator:'blue'}); return;
		}
		this.data = [];

		var dialog = new frappe.ui.Dialog({
			title: __("Create Purchase Return to Supplier"),
			fields: [
				{"fieldtype": "Link", "label": __("Supplier"), "fieldname": "supplier", "options":"Supplier",
					"get_query": function () {
						return {
							filters: {'disabled': '0'}
						}
					}},
					{fieldname: 'items_for_si', fieldtype: 'Table', label: 'Select Items',
					fields: [
						{
							fieldtype:'Data',
							fieldname:'sales_return_no',
							label: __('Sales Return No'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'sales_invoice',
							label: __('Order ID'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_code',
							label: __('Item'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_name',
							label: __('Item name'),
							read_only:1
						},
						{
							fieldtype:'Float',
							fieldname:'qty',
							label: __('Quantity'),
							read_only: 1,
							in_list_view:1
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'uom',
							label: __('UOM')
						},
						{
							fieldtype:'Small Text',
							read_only:1,
							fieldname:'serial_no',
							label: __('Serial No'),
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'batch_no',
							label: __('Batch No')
						}
					],
					data: this.data,
					get_data: function() {
						return this.data;

					}
				},

				{"fieldtype": "Button", "label": __('Create Purchase Return'), "fieldname": "make_purchase_return", "cssClass": "btn-primary"},
			]
		});

		dialog.fields_dict.make_purchase_return.$input.click(function() {
			var args = dialog.get_values();
			let selected_items = dialog.fields_dict.items_for_si.grid.get_selected_children()
			if(selected_items.length == 0) {
				frappe.throw({message: 'Please select Item from Table', title: __('Message'), indicator:'blue'})
			} else if (!args.supplier) frappe.throw({message: 'Please set a Supplier', title: __('Message'), indicator:'blue'})

			let selected_items_list = []
			for(let i in selected_items){
				selected_items_list.push(selected_items[i].item_code)
			}
			dialog.hide();
			return frappe.call({
				type: "GET",
				method: "custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.make_purchase_return",
				args: {
					"source_name": me.frm.doc.name,
					"for_supplier": args.supplier,
					"selected_items": selected_items_list
				},
				freeze: true,
				callback: function(r) {
					if(!r.exc) {
						// var args = dialog.get_values();
						if (args.supplier){
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
						else{
							
						}
					}
				}
			})
		});
		dialog.get_field("items_for_si").grid.only_sortable()
		dialog.get_field("items_for_si").refresh()
		dialog.show();

		frm.doc.items.forEach(function(item) {
			if (item.sales_return_no && !item.purchase_return_no) 
				dialog.fields_dict.items_for_si.df.data.push(item);
		});

		this.data = dialog.fields_dict.items_for_si.df.data;
		dialog.fields_dict.items_for_si.grid.refresh();
	},

	make_replacement_invoice: function(frm){
		//var me = this.frm;
		if (frm.is_dirty() || frm.doc.docstatus < 1){
			frappe.msgprint({message: 'Please save and approve document first', title: __('Message'), indicator:'blue'}); return;
		}
		this.data = [];

		var dialog = new frappe.ui.Dialog({
			title: __("Make Replacement Invoice per Customer per Sales Invoice"),
			fields: [
				{"fieldtype": "Link", "label": __("Sales Invoice"), "fieldname": "sales_invoice", "options":"Sales Invoice",
					"description": "Please make sure you have made Sales Return first",
					"get_query": function () {
						return {
							query:"custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.get_sales_invoice",
							filters: {'parent': frm.doc.name}
						}
				}},

				{fieldname: 'items_for_si', fieldtype: 'Table', label: 'Select Items',
					fields: [
						{
							fieldtype:'Data',
							fieldname:'sales_return_no',
							label: __('Sales Return No'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'sales_invoice',
							label: __('Order ID'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_code',
							label: __('Item'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_name',
							label: __('Item name'),
							read_only:1
						},
						{
							fieldtype:'Float',
							fieldname:'qty',
							label: __('Quantity'),
							read_only: 1,
							in_list_view:1
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'uom',
							label: __('UOM')
						},
						{
							fieldtype:'Small Text',
							read_only:1,
							fieldname:'serial_no',
							label: __('Serial No'),
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'batch_no',
							label: __('Batch No')
						}
					],
					data: this.data,
					get_data: function() {
						return this.data;

					}
				},

				{"fieldtype": "Button", "label": __('Make Replacement Invoice'), "fieldname": "make_replacement_invoice", "cssClass": "btn-primary"},
			]
		});

		dialog.fields_dict.make_replacement_invoice.$input.click(function() {
			var args = dialog.get_values();
			let selected_items = dialog.fields_dict.items_for_si.grid.get_selected_children()
			if(selected_items.length == 0) {
				frappe.throw({message: 'Please select Item from Table', title: __('Message'), indicator:'blue'})
			} else if (!args.sales_invoice) frappe.throw({message: 'Please select a Sales Invoice', title: __('Message'), indicator:'blue'})

			let selected_items_list = []
			var order_no_list = []
			for(let i in selected_items){
				selected_items_list.push(selected_items[i].item_code)
				if (order_no_list.length == 0)order_no_list.push(selected_items[i].sales_invoice)
				else if (order_no_list.includes(selected_items[i].sales_invoice))
					frappe.throw({message: 'Please select items form one Sales Invoice (Order No) only', title: __('Message'), indicator:'blue'})
			}
			dialog.hide();
			return frappe.call({
				type: "GET",
				method: "custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.make_replacement_invoice",
				args: {
					"source_name": me.frm.doc.name,
					//"for_customer": args.customer,
					"sales_invoice": args.sales_invoice,
					"selected_items": selected_items_list,
				},
				freeze: true,
				callback: function(r) {
					if(!r.exc) {
						// var args = dialog.get_values();
						if (args.sales_invoice){
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
						else{
							
						}
					}
				}
			})
		});
		dialog.get_field("items_for_si").grid.only_sortable()
		dialog.get_field("items_for_si").refresh()
		dialog.show();

		/* frm.doc.items.forEach(function(item) {
			if (item.sales_return_no && !item.replacement_invoice) 
				dialog.fields_dict.items_for_si.df.data.push(item);
		});

		this.data = dialog.fields_dict.items_for_si.df.data;
		dialog.fields_dict.items_for_si.grid.refresh(); */

		//filter dialog table
		dialog.fields_dict.sales_invoice.$input.on('input change select paste keyup click', function() {
			console.log('filter sales_invoice on_change..');
			var args = dialog.get_values();
			this.data = dialog.fields_dict.items_for_si.df.data = [];

			frm.doc.items.forEach(function(item) {
				//console.log('item.replacement_invoice = ' + item.replacement_invoice);
				//console.log('args.sales_invoice = ' + args.sales_invoice);
				if (item.sales_invoice && item.sales_return_no && !item.replacement_invoice && item.sales_invoice == args.sales_invoice) 
					dialog.fields_dict.items_for_si.df.data.push(item);
			});
			//if (!args.sales_invoice) dialog.fields_dict.items_for_si.df.data = frm.doc.items;

			this.data = dialog.fields_dict.items_for_si.df.data;
			dialog.fields_dict.items_for_si.grid.refresh();
		});
	},

	make_new_purchase_invoice: function(frm){
		//var me = this.frm;
		if (frm.is_dirty() || frm.doc.docstatus < 1){
			frappe.msgprint({message: 'Please save and approve document first', title: __('Message'), indicator:'blue'}); return;
		}
		this.data = [];

		var dialog = new frappe.ui.Dialog({
			title: __("Receive New Items from Supplier (New Purchase Invoice)"),
			fields: [
				{"fieldtype": "Link", "label": __("Select a Supplier"), "fieldname": "supplier", "options":"Supplier",
					"description": "Please make sure you have made Purchase Return first",
					"get_query": function () {
						return {
							query:"custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.get_supplier",
							filters: {'parent': frm.doc.name}
						}
					}
				},
				{fieldname: 'items_for_si', fieldtype: 'Table', label: 'Select Items',
					fields: [
						{
							fieldtype:'Data',
							fieldname:'purchase_return_no',
							label: __('Purchase Return No'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'sales_invoice',
							label: __('Order ID'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_code',
							label: __('Item'),
							read_only:1,
							in_list_view:1
						},
						{
							fieldtype:'Data',
							fieldname:'item_name',
							label: __('Item name'),
							read_only:1
						},
						{
							fieldtype:'Float',
							fieldname:'qty',
							label: __('Quantity'),
							read_only: 1,
							in_list_view:1
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'uom',
							label: __('UOM')
						},
						{
							fieldtype:'Small Text',
							read_only:1,
							fieldname:'serial_no',
							label: __('Serial No'),
						},
						{
							fieldtype:'Link',
							read_only:1,
							fieldname:'batch_no',
							label: __('Batch No')
						}
					],
					data: this.data,
					get_data: function() {
						return this.data;

					}
				},

				{"fieldtype": "Button", "label": __('Make Purchase Invoice For New Items'), "fieldname": "make_new_purchase_invoice", "cssClass": "btn-primary"},
			]
		});

		dialog.fields_dict.make_new_purchase_invoice.$input.click(function() {
			var args = dialog.get_values();
			let selected_items = dialog.fields_dict.items_for_si.grid.get_selected_children()
			if(selected_items.length == 0) {
				frappe.throw({message: 'Please select Item from Table', title: __('Message'), indicator:'blue'})
			} else if (!args.supplier) frappe.throw({message: 'Please set a Supplier', title: __('Message'), indicator:'blue'})

			let selected_items_list = []
			for(let i in selected_items){
				selected_items_list.push(selected_items[i].item_code)
			}
			dialog.hide();
			return frappe.call({
				type: "GET",
				method: "custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.make_new_purchase_invoice",
				args: {
					"source_name": me.frm.doc.name,
					"for_supplier": args.supplier,
					"selected_items": selected_items_list
				},
				freeze: true,
				callback: function(r) {
					if(!r.exc) {
						// var args = dialog.get_values();
						if (args.supplier){
							var doc = frappe.model.sync(r.message);
							frappe.set_route("Form", r.message.doctype, r.message.name);
						}
						else{
							
						}
					}
				}
			})
		});
		dialog.get_field("items_for_si").grid.only_sortable()
		dialog.get_field("items_for_si").refresh()
		dialog.show();

		//filter dialog table
		dialog.fields_dict.supplier.$input.on('input change select paste keyup click', function() {
			console.log('filter supplier on_change..');
			var args = dialog.get_values();
			this.data = dialog.fields_dict.items_for_si.df.data = [];

			frm.doc.items.forEach(function(item) {
				//console.log('item.replacement_invoice = ' + item.replacement_invoice);
				//console.log('args.sales_invoice = ' + args.sales_invoice);
				if (item.sales_invoice && item.sales_return_no && !item.purchase_invoice && item.supplier == args.supplier) 
					dialog.fields_dict.items_for_si.df.data.push(item);
			});
			//if (!args.sales_invoice) dialog.fields_dict.items_for_si.df.data = frm.doc.items;

			this.data = dialog.fields_dict.items_for_si.df.data;
			dialog.fields_dict.items_for_si.grid.refresh();
		});
	},

	setup: function(frm) {
		frappe.ui.form.States.prototype.setup_help = function(){}
		//$(".dropdown-menu li").not(".user-action").addClass("hide");
		
	},

	refresh: function(frm) {
		//frm.set_df_property("items", "read_only", 1);
		//$(".actions-btn-group").find('.menu-item').hide();

		//frm.page.clear_actions_menu();
		//frm.page.clear_custom_buttons();

		if(!frm.doc.docstatus) {
			/* frm.add_custom_button(__('Create Sales Return'), function() {
				if (frm.is_dirty()){
					frappe.msgprint({message: 'Please save document first', title: __('Message'), indicator:'blue'}); return;
				}
				frappe.model.with_doctype('Sales Invoice', function() {
					var si = frappe.model.get_new_doc('Sales Invoice');
					si.is_return = 1;
					var items = frm.get_field('items').grid.get_selected_children();
					if(!items.length) {
						items = frm.doc.items;
					}
					items.forEach(function(item) {
						if (item.idx==1){
							frappe.msgprint(__("Skip Row " + item.idx + ". Return was made for this item"));
							return false;
						}
						var si_item = frappe.model.add_child(si, 'items');
						if (!si.customer) si.customer = item.customer;
						if (si.customer && si.customer != item.customer){
							frappe.validated = false;
							frappe.throw(__("Multiple Customers found. Please select from 1 (one) customer only")); return;
						}
						si_item.item_code = item.item_code;
						si_item.item_name = item.item_name;
						si_item.description = item.description;
						si_item.qty = item.qty * -1;
						si_item.rate = item.rate
						si_item.uom = item.uom;
						si_item.warehouse = item.warehouse;
						si_item.serial_no = item.serial_no;
						si_item.batch_no = item.batch_no;
						si_item.income_account = item.income_account;
						si_item.expense_account = item.expense_account;
					});
					frappe.set_route('Form', 'Sales Invoice', si.name);
				});
			}); */
		}
		// make sales return invoice
		frm.add_custom_button(__('Make Sales Return (Credit Note)'), () => frm.events.create_sales_return(frm));

		// make purchase return invoice
		frm.add_custom_button(__('Make Purchase Return (Debit Note)'), () => frm.events.create_purchase_return(frm));

		// make replacement invoice
		frm.add_custom_button(__('Make Replacement Invoice'), () => frm.events.make_replacement_invoice(frm));

		// receive new items from Supplier (new purchase invoice)
		frm.add_custom_button(__('Receive New Items from Supplier'), () => frm.events.make_new_purchase_invoice(frm));

		if (frm.doc.docstatus === 1) {
			if (frm.doc.per_transferred < 100) {
				frm.add_custom_button(__('Receive at Warehouse Entry'), function() {
					frappe.model.open_mapped_doc({
						method: "erpnext.stock.doctype.stock_entry.stock_entry.make_stock_in_entry",
						frm: frm
					})
				});
			}
		}

		if ((frm.doc.docstatus===0 && !frm.is_dirty()) || (frm.is_new() && !frm.doc.items)) {
			frm.add_custom_button(__('Sales Invoice'), function() {
				erpnext.utils.map_current_doc({
					method: "custom1.marketplace_flow.doctype.marketplace_return.marketplace_return.get_sales_invoice_items",
					source_doctype: "Sales Invoice",
					target: frm,
					date_field: "posting_date",
					setters: [
						{
							label: "Customer",
							fieldname: "customer",
							fieldtype: "Link",
							options: frm.doc.customer || ''
						},
						{
							label: "AWB No",
							fieldname: "awb_no",
							fieldtype: "Data"
						}
					],
					get_query_filters: {
						docstatus: 1,
						is_return: 0,
						company: frm.doc.company
					}
				})
			}, __("Get items from"));

		}

		if (frm.doc.company) {
			//frm.trigger("toggle_display_account_head");
		}
	},

	company: function(frm) {
		if(frm.doc.company) {
			var company_doc = frappe.get_doc(":Company", frm.doc.company);
			if(company_doc.default_letter_head) {
				frm.set_value("letter_head", company_doc.default_letter_head);
			}
		}
	},

	set_serial_no: function(frm, cdt, cdn, callback) {
		var d = frappe.model.get_doc(cdt, cdn);
		if(!d.item_code && !d.warehouse && !d.qty) return;
		var	args = {
			'item_code'	: d.item_code,
			'warehouse'	: cstr(d.warehouse),
			'stock_qty'	: d.qty
		};
		frappe.call({
			method: "erpnext.stock.get_item_details.get_serial_no",
			args: {"args": args},
			callback: function(r) {
				if (!r.exe && r.message){
					frappe.model.set_value(cdt, cdn, "serial_no", r.message);

					if (callback) {
						callback();
					}
				}
			}
		});
	},

	get_warehouse_details: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];

		if(child.item_code && child.warehouse) {
			frappe.call({
				method: "erpnext.stock.doctype.stock_entry.stock_entry.get_warehouse_details",
				args: {
					"args": {
						'item_code': child.item_code,
						'warehouse': cstr(child.warehouse) || cstr(frm.doc.default_warehouse),
						'serial_no': child.serial_no,
						'qty': child.qty,
						'posting_date': frm.doc.posting_date,
						'company': frm.doc.company
					}
				},
				callback: function(r) {
					if (!r.exc) {
						$.extend(child, r.message);
					}
				}
			});
		}
	},
	
})


frappe.ui.form.on('Marketplace Return Item', {
	qty: function(frm, cdt, cdn) {
		//frm.events.set_serial_no(frm, cdt, cdn, () => {
		//	frm.events.set_basic_rate(frm, cdt, cdn);
		//});
	},

	warehouse: function(frm, cdt, cdn) {
		//frm.events.set_serial_no(frm, cdt, cdn, () => {
			frm.events.get_warehouse_details(frm, cdt, cdn);
			frm.script_manager.trigger("item_code", cdt, cdn);
		//});
	},

	item_code: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (!d.warehouse)d.warehouse = frm.doc.default_warehouse;
		if (!d.qty)d.qty = 1;
		d.batch_no = '';
		d.serial_no = '';

		if(d.item_code) {
			var args = {
				'item_code'		: d.item_code,
				'warehouse'		: cstr(d.warehouse) || frm.doc.default_warehouse,
				'serial_no'		: d.serial_no,
				'company'		: frm.doc.company,
				'qty'			: d.qty || 1
			};

			return frappe.call({
				doc: frm.doc,
				method: "get_item_details",
				args: args,
				callback: function(r) {
					if(r.message) {
						var d = locals[cdt][cdn];
						//console.log(r.message);
						$.each(r.message, function(k, v) {
							if (v) {
								frappe.model.set_value(cdt, cdn, k, v); // qty and it's subsequent fields weren't triggered
							}
						});
						refresh_field("items");

						if (!d.serial_no) {
							erpnext.stock.select_batch_and_serial_no(frm, d);
						}
					}
				}
			});
		} 
	},

	serial_no: function(frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		if (!d.item_code) return;

		frappe.db.get_value('Item', {item_code: d.item_code}, 'has_serial_no', function(val) {
			//console.log('has_serial_no == ' + val.has_serial_no);
			if (val.has_serial_no)
				frappe.model.set_value(cdt, cdn, "qty", d.serial_no.trim().split("\n").length || 1);

		});
	},

	batch_no: function(frm, cdt, cdn) {
		//validate_sample_quantity(frm, cdt, cdn);
	},
});



erpnext.stock.StockEntry = erpnext.stock.StockController.extend({
	setup: function() {
		var me = this;

		this.setup_posting_date_time_check();


		this.frm.fields_dict.items.grid.get_field('item_code').get_query = function() {
			return erpnext.queries.item({is_stock_item: 1});
		};

		this.frm.set_indicator_formatter('item_code',
			function(doc) {
				if (!doc.s_warehouse) {
					return 'blue';
				} else {
					return (doc.qty<=0) ? "green" : "orange"
				}
			})
	},

	onload_post_render: function() {
		var me = this;
		this.set_default_account(function() {
			if(me.frm.doc.__islocal && me.frm.doc.company && !me.frm.doc.amended_from) {
				me.frm.trigger("company");
			}
		});

		this.frm.get_field("items").grid.set_multiple_add("item_code", "qty");
	},

	refresh: function() {
		var me = this;
		//erpnext.toggle_naming_series();
		//this.toggle_related_fields(this.frm.doc);
		//this.show_stock_ledger();
		if (this.frm.doc.docstatus===1 && erpnext.is_perpetual_inventory_enabled(this.frm.doc.company)) {
			//this.show_general_ledger();
		}
		erpnext.hide_company();
		erpnext.utils.add_item(this.frm);
	},

	scan_barcode: function() {
		//let transaction_controller= new erpnext.TransactionController({frm:this.frm});
		//transaction_controller.scan_barcode();
	},

	on_submit: function() {
		//this.clean_up();
	},

	after_cancel: function() {
		//this.clean_up();
	},

	clean_up: function() {
		// Clear Work Order record from locals, because it is updated via Stock Entry
		if(this.frm.doc.work_order &&
			in_list(["Manufacture", "Material Transfer for Manufacture", "Material Consumption for Manufacture"],
				this.frm.doc.purpose)) {
			frappe.model.remove_from_locals("Work Order",
				this.frm.doc.work_order);
		}
	},

	items_add: function(doc, cdt, cdn) {
		var row = frappe.get_doc(cdt, cdn);
		//this.frm.script_manager.copy_from_first_row("items", row, ["expense_account", "cost_center"]);

		//if(!row.s_warehouse) row.s_warehouse = this.frm.doc.from_warehouse;
		//if(!row.t_warehouse) row.t_warehouse = this.frm.doc.to_warehouse;
	},

	items_on_form_rendered: function(doc, grid_row) {
		//erpnext.setup_serial_no();
	},
});

erpnext.stock.select_batch_and_serial_no = (frm, item) => {
	let get_warehouse_type_and_name = (item) => {
		let value = '';
		if(frm.fields_dict.default_warehouse.disp_status === "Write") {
			value = cstr(item.warehouse) || '';
			return {
				type: 'Source Warehouse',
				name: value
			};
		} else {
			value = cstr(item.warehouse) || '';
			return {
				type: 'Target Warehouse',
				name: value
			};
		}
	}

	if(item && !item.has_serial_no && !item.has_batch_no) return;
	//if (frm.doc.purpose === 'Material Receipt') return;

	frappe.require("assets/erpnext/js/utils/serial_no_batch_selector.js", function() {
		new erpnext.SerialNoBatchSelector({
			frm: frm,
			item: item,
			warehouse_details: get_warehouse_type_and_name(item),
		});
	});

}
