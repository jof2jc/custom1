from __future__ import unicode_literals
import frappe
from frappe import _, scrub

from frappe.utils import fmt_money, nowdate, nowtime, now_datetime, flt, cstr, formatdate, get_datetime, add_days, getdate, get_time, get_site_name, time_diff_in_hours
from frappe.utils.dateutils import parse_date
from frappe.model.naming import make_autoname
import json
import datetime
from erpnext.setup.utils import get_exchange_rate
from erpnext.accounts.utils import get_account_currency, get_balance_on
import erpnext.accounts.utils
from re import sub
from decimal import Decimal
from frappe.model.mapper import get_mapped_doc
from frappe.utils.response import build_response
from frappe.api import get_request_form_data
import frappe.handler
import frappe.client
import requests


#def shoutout():
#print 'yay!'

#def build_my_thing():
#erpnext.accounts.utils.test = shoutout


def session_start():
	frappe.msgprint("hiiiiiiiiiiiiiiii")

@frappe.whitelist()
def test_rpc():
	#data = get_request_form_data()
	#return frappe.local.request.get_data()
	#data = requests.request.get_data()

	frappe.local.response.update({"mytest":"yesy"})
	return build_response("json")


def validate_school_fees(self, method):
	minimum_payment = frappe.get_value("Fee Structure", self.fee_structure, "minimum_payment") or 0.0
	if minimum_payment and not self.minimum_payment:
		if flt(minimum_payment) > flt(self.outstanding_amount):
			self.minimum_payment = flt(self.outstanding_amount)
		else:
			self.minimum_payment = flt(minimum_payment)


def before_insert_feepayment(self, method):
	msg = ""
	fees = None
	
	#Preset fields
	self.parenttype = "Fees"
	self.parentfield = "payments"
	
	if not self.parent:
		msg = "invoice No is empty or not valid"
	elif frappe.db.exists(self.doctype,{"name":self.requestid}):
		msg = "Duplicate RequestID %s. Rejected" % (self.requestid)
	elif not self.paidamount:
		msg = "Paid Amount is mandatory"
	elif not self.reference:
		msg = "Reference No is mandatory"
	elif not self.transactiondate:
		msg = "Transaction Date is mandatory"

	else:
		#parent = frappe.get_value("Fees",{"name":self.companycode + self.customernumber},"name") or ""
		parent = frappe.get_value("Fees",{"name":self.parent},"name") or ""
		if parent:
			fees = frappe.get_doc("Fees",parent)

		if not fees:
			msg = "Could not get invoice detail"
		else:
			if flt(self.paidamount) > flt(fees.outstanding_amount):
				msg = "Overpaid. Payment should be less than or equal %s" % (cstr(fmt_money(fees.outstanding_amount)))
			elif flt(self.paidamount) < flt(fees.minimum_payment):
				msg = "Minimum Payment is %s" % (cstr(fmt_money(fees.minimum_payment)))
	if msg:
		raise frappe.ValidationError(msg)

def after_insert_feepayment(self, method):
	msg = ""
	fees = None

	
	#parent = frappe.get_value("Fees",{"name":self.companycode + self.customernumber},"name") or ""
	parent = frappe.get_value("Fees",{"name":self.parent},"name") or ""
	if parent:
		fees = frappe.get_doc("Fees",parent)

	if not fees:
		msg = "Could not get invoice detail"

	if msg:
		raise frappe.ValidationError(msg)

	#if fees and not frappe.get_value("Payment Entry",{"reference_no":self.reference, "docstatus": "1"},"name"):
	if fees and not self.payment_entry:
		msg = ""
		company = frappe.db.get_single_value('Global Defaults', 'default_company')
		mode_of_payment = frappe.db.get_value('Mode of Payment', {'enabled':1, 'for_va_payment':1}, "name") or ""
		paid_to_account = frappe.db.get_value('Mode of Payment Account', {'parent':mode_of_payment, 'company':company}, "default_account")

		payment_entry = frappe.get_doc({"doctype":"Payment Entry","naming_series":self.parent + "~PE/.YY./.MM./.###",
			"company":company, "reference_no":self.reference,"reference_date":getdate(self.transactiondate),
			"payment_type":"Receive","posting_date":getdate(self.transactiondate) or nowdate(),"party_type":"Student",
			"party":fees.student,"mode_of_payment":mode_of_payment,"paid_from":fees.receivable_account,"paid_to":paid_to_account,
			"paid_amount":flt(self.paidamount),"received_amount":flt(self.paidamount),
			"references":[{"reference_doctype":"Fees","reference_name":self.parent,"allocated_amount":self.paidamount}]})

		if payment_entry:
			self.db_set("payment_entry",payment_entry.name)
			#self.save()
			
			payment_entry.flags.ignore_permissions = True
			payment_entry.insert()
			self.db_set("payment_entry",payment_entry.name)
			payment_entry.submit()

		if not self.payment_entry:
			msg = "Something got wrong. Payment Entry is empty"
			raise frappe.ValidationError(msg)

		if not msg:
			frappe.db.commit()



def update_school_fee_payment(self, method):
	if self.docstatus > 0 and frappe.get_value("Company",self.company,"domain") == "Education":
		msg = ""
		for d in self.references:
			data = {}
			if not frappe.get_value("FeePayment",{"parent":d.reference_name, "payment_entry":self.name},"payment_entry"):
				feepayment = frappe.get_doc({
					"doctype": "FeePayment",
					"requestid": frappe.generate_hash("FeePayment",16),
					"reference": self.name,
					"transactiondate": self.posting_date,
					"parenttype": "Fees",
					"parentfield": "payments",
					"parent": d.reference_name,
					"customername": self.party_name or self.party,
					"currencycode":"IDR",
					"totalamount": d.total_amount,
					"paidamount": d.allocated_amount,
					"payment_entry": self.name
				})
				idx = frappe.db.sql("""select idx from `tabFeePayment` where parent=%s order by idx desc limit 1""", (d.reference_name),as_dict=0) or 0.0
				if idx: 
					feepayment.idx = flt(idx[0][0]) + 1
				

				feepayment.insert()
			else:
				msg = 'This payment reference "%s" exists in Student Fees "%s"' % (d.parent, d.reference_name)
				#raise frappe.ValidationError(msg)

			if self.docstatus == 2:
				for row in frappe.db.get_values("FeePayment", {"payment_entry":self.name, "parent": d.reference_name}, "name"):
					feepayment = frappe.get_doc("FeePayment",row[0])
					if feepayment: feepayment.delete()
		if not msg:		
			frappe.db.commit()
	



''' OLD '''
@frappe.whitelist()
def autocreate_school_fees_payment(self, method):
	#frappe.msgprint("Payment %s with Reference No %s is submitted successfully" % (cstr(fmt_money(self.paid_amount)), self.reference_no))
	msg = "Payment %s with Reference No %s is submitted successfully" % (cstr(fmt_money(self.paid_amount)), self.reference_no)
	frappe.db.commit()
	frappe.local.response.update({"myteststatus":msg})
	return build_response("json")

def before_insert_school_fees_payment(self, method):
	msg = ""
	fees = None
	
	#Preset fields
	self.parenttype = "Fees"
	self.parentfield = "payments"
	
	if not self.parent:
		msg = "invoice No is empty or not valid"
	elif frappe.db.exists(self.doctype,{"name":self.reference_no}):
		msg = "Duplicate Reference No %s. Rejected" % (self.reference_no)
	elif not self.paid_amount:
		msg = "Paid Amount is mandatory"
	elif not self.reference_no:
		msg = "Reference No is mandatory"
	elif not self.reference_date:
		msg = "Reference Date is mandatory"

	else:
		fees = frappe.get_doc("Fees",self.parent)
		if not fees:
			msg = "Could not get invoice detail"
		else:
			if flt(self.paid_amount) > flt(fees.outstanding_amount):
				msg = "Overpaid. Payment should be less than or equal %s" % (cstr(fmt_money(fees.outstanding_amount)))
			elif flt(self.paid_amount) < flt(fees.minimum_payment):
				msg = "Minimum Payment is %s" % (cstr(fmt_money(fees.minimum_payment)))
	if msg:
		frappe.throw(msg)

	if fees:
		msg = ""
		company = frappe.db.get_single_value('Global Defaults', 'default_company')
		paid_to_account = frappe.db.get_value('Mode of Payment Account', {'parent':'Cash', 'company':company}, "default_account")

		payment_entry = frappe.get_doc({"doctype":"Payment Entry","naming_series":self.parent + "~PE/.YY./.MM./.###",
			"company":company, "reference_no":self.reference_no,"reference_date":getdate(self.reference_date),
			"payment_type":"Receive","posting_date":nowdate(),"party_type":"Student",
			"party":fees.student,"mode_of_payment":"Cash","paid_from":fees.receivable_account,"paid_to":paid_to_account,
			"paid_amount":flt(self.paid_amount),"received_amount":flt(self.paid_amount),
			"references":[{"reference_doctype":"Fees","reference_name":self.parent,"allocated_amount":self.paid_amount}]})

		try:
			payment_entry.flags.ignore_permissions = True
			payment_entry.insert()
			payment_entry.submit()
			#frappe.db.commit()
			msg = "Payment %s with Reference No %s is submitted successfully.Payment Voucher No: %s" % (cstr(fmt_money(self.paid_amount)), self.reference_no, payment_entry.name)

			if payment_entry:
				self.payment_entry = payment_entry.name

		except Exception as e:
			msg = cstr(e)
			error_trace = frappe.get_traceback()
			if error_trace:
				error_log_doc = frappe.log_error(error_trace)
			frappe.db.rollback()
	
	if not msg:
		frappe.throw("Server Error. Please contact Administrator")
		