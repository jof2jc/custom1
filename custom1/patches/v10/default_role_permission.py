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
	frappe.db.sql ("""DELETE from `tabCustom DocPerm` where parenttype='DocType' 
			and role in ('Accounts User','Accounts Manager','Sales Manager','Sales User','Sales Master Manager',
				'Purchase User','Purchase Manager','Purchase Master Manager','Material User',
				'Material Master Manager','Material Manager')
			and parent not in ('Sales Order','Delivery Note','Cost Center','Territory','testdoctype','Sales Taxes and Charges Template',
			'Account','Customer Group','Customer','Terms and Conditions','Supplier','Supplier Type','Mode of Payment','Item Group','Currency',
			'Currency Exchange','Brand','Purchase Taxes and Charges Template','Party Type','Price List','Address','Contact','Quotation',
			'Payment Term','Payment Terms Template','Journal Entry','Sales Invoice','Purchase Invoice','Payment Entry','Stock Ledger Entry',
			'Fiscal Year','GL Entry','Tax Rule','ToDo','Note','Period Closing Voucher','Payment Reconciliation','Item','UOM','Warehouse',
			'Stock Reconciliation','Purchase Receipt','Stock Entry','Bin','Stock Settings','IMEI Stock Opname','Purchase Order',
			'Item Price','Sales Person')

		""")