from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time
from frappe.utils.dateutils import parse_date
from frappe.model.naming import make_autoname
import json
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.utils import get_account_currency, get_balance_on
import erpnext.accounts.utils
from re import sub
from decimal import Decimal


def execute():
	frappe.db.sql ("""DELETE from `tabDesktop Icon`	where standard=0 and module_name not in ('Accounts','Selling','Buying','Stock','Setup')""")
	#frappe.db.sql ("""Update `tabDesktop Icon` set hidden=0, blocked=0 where standard=1""")
	#frappe.db.sql ("""Update `tabDesktop Icon` set standard=1, hidden=1, blocked=1 where module_name in ('Accounts','Selling','Buying','Stock','Setup')""")

	frappe.db.sql ("""Update `tabDesktop Icon` set hidden=1, blocked=1 where 
			module_name in ('File Manager','Tools','ptdun','Report','Website','CRM','Integrations',
			'Email Inbox','Issue','Lead','Profit and Loss Statement','Profit and Loss Statment','Human Resources','Manufacturing', 'POS',
			'Leaderboard','Support','Learn','Maintenance','Account Receivable','Account Payable',
			'Student','Student Group', 'Course Schedule','Sales Register', 'Student Attendance', 'Course', 'Student Attendance Tool', 
			'Program', 'Student Applicant', 'Examination', 'Assessment', 'Fees', 'Instructor', 'Room', 'Schools', 'Healthcare',
			'Education', 'Hub', 'Data Import Tool', 'Restaurant', 'Agriculture', 'Crop', 'Crop Cycle', 'Fertilizer',
			'Land Unit', 'Disease', 'Plant Analysis', 'Soil Analysis', 'Water Analysis', 'Soil Texture', 'Weather', 'Grant Application',
			'Donor', 'Volunteer', 'Member','Chapter', 'Delivery Note Trends', 'Non Profit')""")

	#frappe.db.sql ("""Update `tabDesktop Icon` set hidden=1, blocked=1 where 
	#		module_name in ('Custom1','Item','Customer','Supplier','Sales Order','Delivery Note','Sales Invoice',
	#		'Purchase Order','Purchase Receipt','Purchase Invoice','Payment Entry','Journal Entry','Note','ToDo', 'Task',
	#		'Stock Entry','Stock Reconciliation','Item Summary','Item Price','Chart of Accounts','Item wise Sales Register',
	#		'Stock Reorder Projection','IMEI', 'Project','Projects', 'Product Bundle', 'Warehouse', 'Terms and Conditions', 
	#		'Sales Overview By Period', 'Adresses and Contacts', 'Material Request', 'Quotation', 'Supplier Quotation')""")

	#frappe.db.sql ("""Update `tabDesktop Icon` set hidden=1 where standard=1 and 
	#		module_name in ('Accounts','Selling','Buying','Stock','Setup')""")
	
	if frappe.db.exists("DocType", "Payment Term"):
		frappe.db.sql ("""Update `tabCustomer Group` set payment_terms=''""")
		frappe.db.sql ("""Update `tabSupplier Type` set payment_terms=''""")
		frappe.db.sql ("""Update `tabCompany` set payment_terms=''""")

	doc = frappe.get_doc("Stock Settings")
	doc.show_barcode_field = 0
	doc.save()

	doc = frappe.get_doc("Website Settings")
	doc.home_page = "desk"
	doc.save()