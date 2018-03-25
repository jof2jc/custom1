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
		"Property Setter"
]
'''
fixtures = [                                                                                                                                                  
	        {
        		"doctype": "Property Setter",
		        "filters": {
        				"doc_type": ["in", ["Sales Invoice","Purchase Invoice","Sales Order","Purchase Order","Item","Stock Settings"]],
				        "field_name": ["in", ["subscription_section","raw_materials_supplied","is_item_from_hub","hub_publishing_sb","show_barcode_field"]]
        		}

    		},
		{
        		"doctype": "Custom Field",
		        "filters": {
        				"dt": ["in", ["Sales Invoice"]],
					"name": ["in", ["Sales Invoice-get_items", "Sales Invoice-serial_nos","Sales Invoice-clear"]]
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

# include js, css files in header of desk.html
# app_include_css = "/assets/custom1/css/custom1.css"
# app_include_js = "/assets/custom1/js/custom1.js"

website_context = {
	"splash_image": "/assets/custom1/images/splash.png"
}

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
doc_events = {
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
	"validate": "custom1.custom1.custom1.si_validate",
	"before_insert": "custom1.custom1.custom1.si_validate"
	#"before_save": "custom1.custom1.custom_imei.populate_item_details"
    },
    "Purchase Invoice": {
        "on_submit": "custom1.custom1.custom_imei.set_return_details",
	"on_cancel": "custom1.custom1.custom_imei.set_return_details"
    },
    "Payment Entry": {
        "on_submit": "custom1.custom1.custom_imei.imp_update_installment_payment_details",
	"before_cancel": "custom1.custom1.custom_imei.imp_before_cancel_installment_payment"
    }
}


# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"custom1.tasks.all"
# 	],
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

