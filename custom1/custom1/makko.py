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



def update_linked_docs(self, method):
	if "MAKKO" not in self.company.upper():
		return

	for d in self.items:
		dn = frappe.get_doc("Delivery Note",d.delivery_note)
		for dn_item in dn.items:
			if dn_item.item_code == d.item_code:
				dn_item.db_set("sales_invoice_link",d.parent)