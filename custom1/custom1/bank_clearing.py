from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time, get_site_name



def update_bank_clearing_voucher(self, method):
	if self.docstatus == 2:
		is_valid = 0
		if "clearing_voucher" in frappe.db.get_table_columns("Payment Entry") and "clearing_voucher" in frappe.db.get_table_columns("Journal Entry"):
			is_valid = 1
			
		if is_valid:
			for d in frappe.db.sql("""Select name from `tabPayment Entry` where clearing_voucher=%s and docstatus=1""",(self.name), as_dict=1):
				payment_entry = frappe.get_doc("Payment Entry",d.name)
				payment_entry.db_set("clearing_voucher","")
				payment_entry.db_set("clearance_date",None)

			for d in frappe.db.sql("""Select name from `tabJournal Entry` where clearing_voucher=%s and docstatus=1""",(self.name), as_dict=1):
				payment_entry = frappe.get_doc("Journal Entry",d.name)
				payment_entry.db_set("clearing_voucher","")
				payment_entry.db_set("clearance_date",None)
				
			frappe.db.commit()