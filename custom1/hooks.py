# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "custom1"
app_title = "Custom1"
app_publisher = "jonathan"
app_description = "test"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "jof2jc@gmail.com"
app_version = "0.0.1"
'''
fixtures = [    
		{
        		"doctype": "User",
			"filters": {
        				"email": ["=", ["mitra_gemilang16@yahoo.com"]],
					"field_name": ["in", ["blocked_modules"]]
        		}

    		},
		{
        		"doctype": "Report",
		        "filters": {
        				"name": ["in", ["SINV","PINV","DLN","SO","QUO","PREC","PO"]]
        		}

    		},                                                                                                                                              
	        {
        		"doctype": "Property Setter",
		        "filters": {
        				"doc_type": ["in", ["Sales Invoice","Purchase Invoice","Sales Order","Purchase Order"]],
				        "field_name": ["in", ["subscription_section","raw_materials_supplied"]]
        		}

    		},
		{
        		"doctype": "Custom Field",
		        "filters": {
        				"dt": ["in", ["Sales Invoice"]],
					"name": ["in", ["Sales Invoice-get_items", "Sales Invoice-serial_nos","Sales Invoice-clear"]]
        		}

    		},
		"Property Setter"
]
'''
fixtures = [  
		{
			"doctype": "Custom Field",
		        "filters": {
        				"dt": ["in", ["Payment Entry Reference", "Payment Entry", "Sales Invoice"]],
				        "fieldname": ["in", ["import_time","actual_shipping_fee","awb_no","courier","cb_marketplace2","sb_marketplace","cb_marketplace","ship_to","recipient","recipient_number","ordered_amount","no_online_order","insurance_fee","shipping_fee","get_invoices","online_order_ids"]]
        		}
    		},     
		{
			
			"doctype": "Custom Script",
		        "filters": {
        				"dt": ["in", ["Payment Entry", "Data Import"]]
        		}
    		},
		{
        		"doctype": "Property Setter",
		        "filters": {
        				"doc_type": ["in", ["Payment Entry Reference","Data Import","Stock Entry","Stock Entry Detail","Sales Invoice","Purchase Invoice","Sales Order","Delivery Note","Purchase Order","Item","Stock Settings","Sales Order Item","Delivery Note Item","Sales Invoice Item","Purchase Order Item","Purchase Receipt Item","Purchase Invoice Item"]],
				        "field_name": ["in", ["bom","serial_no_batch","serial_no","batch_no","project","discount_amount","project","reference_doctype","submit_after_import","overwrite","only_update","skip_errors","ignore_encoding_errors","no_email","get_items_from_open_material_requests","is_subcontracted","pos_profile","source_warehouse_address","target_warehouse_address","is_fixed_asset","foreign_trade_Details","tolerance","is_item_from_hub","customer_po_details","subscription_section","raw_materials_supplied","is_item_from_hub","hub_publishing_sb","show_barcode_field","item_weight_details"]]
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
        				"name": ["in", ["AWB"]]
        		}
    		}
]
	
# Includes in <head>
# ------------------

app_include_js = [
	"assets/js/desk1.min.js",
	"assets/js/list1.min.js",
	"assets/js/form1.min.js",
	"assets/js/erpnext1.min.js"
]

app_include_css = [
	"assets/css/desk1.min.css"
]

#after_migrate = ["custom1.custom1.custom1.reset_default_icons"]

# include js, css files in header of desk.html
# app_include_css = "/assets/custom1/css/custom1.css"
# app_include_js = "/assets/custom1/js/custom1.js"

website_context = {
	"splash_image": "/assets/custom1/images/splash.png"
}

#doctype_list_js = {"Sales Invoice":"public/js/sales_invoice_list.js"}

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
on_session_creation = ["custom1.custom1.custom1.payment_reconciliation_onload"]

doc_events = {
    "Batch": {
	"autoname": "custom1.custom1.custom1.batch_autoname"
    },
    "Item": {
	"validate": "custom1.custom1.custom1.item_validate"
    },
    "Stock Entry": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details"
    },
    "Sales Invoice": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details",
	"before_insert": "custom1.custom1.custom1.si_before_insert",
	"validate": "custom1.custom1.custom1.si_validate"
    },
    "Purchase Invoice": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details"
    },
    "Payment Entry": {
        "on_submit": "custom1.custom1.custom_imei.imp_update_installment_payment_details",
	"before_cancel": "custom1.custom1.custom_imei.imp_before_cancel_installment_payment"
	#"onload": "custom1.custom1.custom1.get_outstanding_invoices_onload_pe"
    },
    "Payment Reconciliation": {
	"onload": "custom1.custom1.custom1.get_outstanding_invoices_onload_pe"
    }
}


# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
 		"custom1.custom1.custom1.delete_old_docs_daily"
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
override_whitelisted_methods = {
 	"erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents": "custom1.custom1.custom1.get_outstanding_reference_documents2"
}

