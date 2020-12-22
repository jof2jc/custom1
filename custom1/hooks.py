# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

app_name = "custom1"
app_title = "Custom1"
app_publisher = "jonathan"
app_description = "test"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "jof2jc@gmail.com"
app_version = "0.0.1"

fixtures = [    
		{
        		"doctype": "Custom Script"
    		}
]

'''
fixtures = [    
		{
        		"doctype": "Custom Field",
		        "dt": ["in", ["Journal Entry"]],
				        "fieldname": ["in", ["sc_expenses","expenses"]]
    		}
]

'''
'''
fixtures = [    
		{
        		"doctype": "Property Setter",
		        "filters": {
        				"doc_type": ["in", ["Sales Order","Purchase Order","Purchase Receipt","Purchase Invoice","Delivery Note",
						"Sales Invoice","Quotation", "Quotation Item","Payment Entry Reference","Data Import","Stock Entry",
						"Stock Entry Detail","Sales Invoice","Purchase Invoice","Sales Order","Delivery Note","Purchase Order",
						"Item","Stock Settings","Sales Order Item","Delivery Note Item","Sales Invoice Item","Purchase Order Item",
						"Purchase Receipt Item","Purchase Invoice Item"
					]],
				        "field_name": ["in", ["payment_schedule_section","item_code","shipping_rule","bom","serial_no_batch","serial_no",
						"batch_no","project","discount_amount","project","reference_doctype","submit_after_import","overwrite",
						"only_update","skip_errors","ignore_encoding_errors","no_email","get_items_from_open_material_requests",
						"is_subcontracted","pos_profile","source_warehouse_address","target_warehouse_address","is_fixed_asset",
						"foreign_trade_Details","tolerance","is_item_from_hub","customer_po_details","subscription_section",
						"raw_materials_supplied","is_item_from_hub","hub_publishing_sb","show_barcode_field","item_weight_details",
						"coupon_code","transporter_info","installed_qty","sales_team_section_break","taxes_section","to_warehouse"
					]]
        		}
    		}
]
'''
'''
fixtures = [  
		{
			"doctype": "Custom Field",
		        "filters": {
        				"dt": ["in", ["Customer","Company","Payment Entry Reference", "Payment Entry", "Sales Invoice","Sales Invoice Item"]],
				        "fieldname": ["in", ["alamat_npwp","dropshipper","lazada_sku","discount_marketplace","shipping_fee","picked_and_packed","is_online_shop","generate_awb_barcode","import_time","actual_shipping_fee","awb_no","courier","cb_marketplace2","sb_marketplace","cb_marketplace","ship_to","recipient","recipient_number","ordered_amount","no_online_order","insurance_fee","shipping_fee","get_invoices","online_order_ids"]]
        		}
    		},     
		{
			
			"doctype": "Custom Script",
		        "filters": {
        				"dt": ["in", ["Payment Entry", "Data Import","Pick and Pack"]]
        		}
    		},
		{
        		"doctype": "Property Setter",
		        "filters": {
        				"doc_type": ["in", ["Quotation Item","Payment Entry Reference","Data Import","Stock Entry","Stock Entry Detail","Sales Invoice","Purchase Invoice","Sales Order","Delivery Note","Purchase Order","Item","Stock Settings","Sales Order Item","Delivery Note Item","Sales Invoice Item","Purchase Order Item","Purchase Receipt Item","Purchase Invoice Item"]],
				        "field_name": ["in", ["item_code","shipping_rule","bom","serial_no_batch","serial_no","batch_no","project","discount_amount","project","reference_doctype","submit_after_import","overwrite","only_update","skip_errors","ignore_encoding_errors","no_email","get_items_from_open_material_requests","is_subcontracted","pos_profile","source_warehouse_address","target_warehouse_address","is_fixed_asset","foreign_trade_Details","tolerance","is_item_from_hub","customer_po_details","subscription_section","raw_materials_supplied","is_item_from_hub","hub_publishing_sb","show_barcode_field","item_weight_details"]]
        		}
    		},
		{
			"doctype": "Custom DocPerm",
		        "filters": {
        				"role": ["in", ["Material User"]]
        		}
    		},
		{
			"doctype": "Report",
		        "filters": {
        				"name": ["in", ["AWB","SKU"]]
        		}
    		}
]
'''	
# Includes in <head>
# ------------------

app_include_js = [
	"assets/js/desk1.min.js",
	"assets/js/list1.min.js",
	"assets/js/form1.min.js",
	"assets/js/erpnext1.min.js",
	"assets/js/report1.min.js",
	"assets/js/zplbrowserprint.min.js"
]

app_include_css = [
	"assets/css/desk1.min.css"
]

doctype_list_js = {
	"Sales Invoice": "public/js/erpnext/list/sales_invoice_list.js",
	"Data Import":"public/js/frappe/list/data_import_list.js"
}

#after_migrate = ["custom1.custom1.custom1.reset_default_icons"]

# include js, css files in header of desk.html
# app_include_css = "/assets/custom1/css/custom1.css"
# app_include_js = "/assets/custom1/js/custom1.js"

website_context = {
	"favicon": "/assets/custom1/images/favicon-256.png",
	"splash_image": "/assets/custom1/images/splash.png"
}

website_route_rules = [
	{"from_route": "/studentfees", "to_route": "FeeBill"},
	{"from_route": "/studentfees/<path:name>", "to_route": "student_fees_info",
		"defaults": {
			"doctype": "Fees",
			"parents": [{"label": _("Student Fee List"), "route": "studentfees"}]
		}
	},
	{"from_route": "/studentscorecard", "to_route": "Student Score Card"},
	{"from_route": "/studentscorecard/<path:name>", "to_route": "student_score_card_info",
		"defaults": {
			"doctype": "Student Score Card",
			"parents": [{"label": _("Student Score Card Report"), "route": "studentscorecard"}]
		}
	}
]

#on_session_creation = [
#	"custom1.custom1.login.redirect_student_guardian_portal"
#]

# include js, css files in header of web template
# web_include_css = "/assets/custom1/css/custom1.css"
# web_include_js = "/assets/custom1/js/custom1.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "custom1.install.before_install"
# after_install = "custom1.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "custom1.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }
#on_session_creation = ["custom1.custom1.custom1.payment_reconciliation_onload"]

doc_events = {
    "Batch": {
	"autoname": "custom1.custom1.custom1.batch_autoname"
    },
    "Item": {
	"validate": "custom1.custom1.custom1.item_validate"
    },
    "Payment Entry": {
	"validate": "custom1.custom1.custom1.set_si_autoname"
    },
    "*": {
	"autoname": "custom1.custom1.custom1.set_si_autoname"
    },
    "Stock Entry": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details",
	"after_insert": "custom1.custom1.custom1.submit_after_save"
    },
    "Sales Invoice": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_submit": "custom1.custom1.makko.update_linked_docs",
	"on_submit": "custom1.marketplace_flow.marketplace_flow.update_marketplace_return_on_sales_invoice_submit_cancel",
	"before_cancel": "custom1.marketplace_flow.marketplace_flow.update_marketplace_return_on_sales_invoice_submit_cancel",
	"before_submit": "custom1.custom1.custom1.si_before_submit",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details",
	#"before_cancel": "custom1.custom1.custom1.si_before_cancel",
	"before_insert": "custom1.custom1.custom1.si_before_insert",
	"validate": "custom1.custom1.custom1.si_validate",
	"before_print": "custom1.custom1.custom1.update_print_counter1",
	"on_update": "custom1.custom1.custom1.si_after_save",
	"on_update_after_submit": "custom1.custom1.custom1.si_on_update_after_submit"
    },
    "Purchase Invoice": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details",
	"on_submit": "custom1.marketplace_flow.marketplace_flow.update_marketplace_return_on_purchase_invoice_submit_cancel",
	"before_cancel": "custom1.marketplace_flow.marketplace_flow.update_marketplace_return_on_purchase_invoice_submit_cancel"
    },
    "Payment Entry": {
        #"on_submit": "custom1.custom1.custom_imei.imp_update_installment_payment_details",
	"before_submit": "custom1.custom1.school_fees.update_school_fee_payment",
	"on_cancel": "custom1.custom1.school_fees.update_school_fee_payment"
	#"before_cancel": "custom1.custom1.custom_imei.imp_before_cancel_installment_payment"
	#"onload": "custom1.custom1.custom1.get_outstanding_invoices_onload_pe"
    },
    "Payment Reconciliation": {
	"onload": "custom1.custom1.custom1.get_outstanding_invoices_onload_pe"
    },
    "Fees": {
	#"on_update_after_submit": "custom1.custom1.school_fees.autocreate_school_fees_payment",
	"validate": "custom1.custom1.school_fees.validate_school_fees"
    },
    "FeePayment": {
	"before_insert": "custom1.custom1.school_fees.before_insert_feepayment",
	"after_insert": "custom1.custom1.school_fees.after_insert_feepayment"
    },
    "Guardian": {
	"validate": "custom1.my_school.my_school.auto_create_user"
    },
    "Instructor": {
	"validate": "custom1.my_school.my_school.auto_create_user"
    },
}


# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
 		"custom1.custom1.custom1.delete_old_docs_daily1",
		"custom1.custom1.custom1.update_default_fiscal_year"
	]
}
# 	"daily": [
# 		"custom1.tasks.daily"
# 	],
# 	"hourly": [
# 		"custom1.tasks.hourly"
# 	],
# 	"weekly": [
# 		"custom1.tasks.weekly"
# 	]
# 	"monthly": [
# 		"custom1.tasks.monthly"
# 	]
# }


# Testing
# -------

# before_tests = "custom1.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
#override_whitelisted_methods = {
# 	"erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents": "custom1.custom1.custom1.get_outstanding_reference_documents2"
#}

