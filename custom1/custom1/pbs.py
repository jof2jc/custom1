# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, nowdate, fmt_money, nowtime, cstr
from frappe import msgprint, _
from frappe.model.document import Document
import json, ast
from erpnext.accounts.party import get_party_account
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account
from erpnext.setup.utils import get_exchange_rate

@frappe.whitelist()
def get_reference_details(reference_doctype, reference_name, party_account_currency):
	total_amount = outstanding_amount = exchange_rate = None
	ref_doc = frappe.get_doc(reference_doctype, reference_name)
	company_currency = ref_doc.get("company_currency")

	if reference_doctype == "Fees":
		total_amount = ref_doc.get("grand_total")
		exchange_rate = 1
		outstanding_amount = ref_doc.get("outstanding_amount")
	elif reference_doctype == "Journal Entry" and ref_doc.docstatus == 1:
		total_amount = ref_doc.get("total_amount")
		if ref_doc.multi_currency:
			exchange_rate = get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)
		else:
			exchange_rate = 1
			#outstanding_amount = get_outstanding_on_journal_entry(reference_name)
	elif reference_doctype != "Journal Entry":
		if party_account_currency == company_currency:
			if ref_doc.doctype == "Expense Claim":
				total_amount = ref_doc.total_sanctioned_amount
			elif ref_doc.doctype == "Employee Advance":
				total_amount = ref_doc.advance_amount
			else:
				total_amount = ref_doc.base_grand_total
			exchange_rate = 1
		else:
			total_amount = ref_doc.grand_total

			# Get the exchange rate from the original ref doc
			# or get it based on the posting date of the ref doc
			exchange_rate = ref_doc.get("conversion_rate") or \
				get_exchange_rate(party_account_currency, company_currency, ref_doc.posting_date)

		if reference_doctype in ("Sales Invoice", "Purchase Invoice"):
			outstanding_amount = ref_doc.get("outstanding_amount")
		elif reference_doctype == "Expense Claim":
			outstanding_amount = flt(ref_doc.get("total_sanctioned_amount")) \
				- flt(ref_doc.get("total_amount+reimbursed")) - flt(ref_doc.get("total_advance_amount"))
		elif reference_doctype == "Employee Advance":
			outstanding_amount = ref_doc.advance_amount - flt(ref_doc.paid_amount)
		else:
			outstanding_amount = flt(total_amount) - flt(ref_doc.advance_paid)
	else:
		# Get the exchange rate based on the posting date of the ref doc
		exchange_rate = get_exchange_rate(party_account_currency,
			company_currency, ref_doc.posting_date)

	return frappe._dict({
		"due_date": ref_doc.get("due_date"),
		"posting_date": ref_doc.get("posting_date") or ref_doc.get("transaction_date"),
		"total_amount": total_amount,
		"outstanding_amount": outstanding_amount,
		"exchange_rate": exchange_rate
	})

@frappe.whitelist()
def update_clearance_date2(bank_account, payment_entries=[]):

	#payment_entries = payment_entries.replace("'", '"').replace('u"', '"')
	#frappe.msgprint("payment_entries : " + payment_entries)

	data = ast.literal_eval(payment_entries)
	#frappe.msgprint(cstr(data))

	msg = ""

	for d in data:
		d=frappe._dict(d)
		#frappe.msgprint(cstr(d))
		if d.clearance_date and d.clearance_account and d.cheque_number:
			if not d.payment_document:
				frappe.throw(_("Row #{0}: Payment document is required to complete the trasaction"))
			elif d.payment_entry and frappe.get_value(d.payment_document,{"name":d.payment_entry, "docstatus":1},"clearance_date"):
				msg = msg + d.payment_document + " " + d.payment_entry + " was already cleared\n"
				continue

			if d.cheque_date and getdate(d.clearance_date) < getdate(d.cheque_date):
				frappe.throw(_("Row #{0}: Clearance date {1} cannot be before Cheque Date {2}")
					.format(d.idx, d.clearance_date, d.cheque_date))

			debit_amount=0.0
			credit_amount=0.0

			ref_doc = frappe.get_doc("GL Entry",{"account": bank_account,"voucher_type": d.payment_document, "voucher_no": d.payment_entry})

			if ref_doc.debit_in_account_currency and not ref_doc.credit_in_account_currency:
				credit_amount= ref_doc.debit_in_account_currency
			elif not ref_doc.debit_in_account_currency and ref_doc.credit_in_account_currency:
				debit_amount= ref_doc.credit_in_account_currency

			cheque_no = ""
			if d.payment_document == "Payment Entry":
				cheque_no = frappe.db.get_value("Payment Entry", d.payment_entry, "reference_no") or ""
			elif d.payment_document == "Journal Entry":
				cheque_no = frappe.db.get_value("Journal Entry", d.payment_entry, "cheque_no") or ""

			if ref_doc:
				jv = frappe.new_doc("Journal Entry")
				jv.flags.ignore_permissions = True
				jv.cheque_no = cheque_no
				jv.cheque_date = d.clearance_date
				jv.naming_series = "CLRG/.YY.MM./.###"
				jv.posting_date = d.clearance_date
				jv.posting_time = nowtime()
				jv.voucher_type = "Journal Entry"
				jv.title = "Cheque/Giro Clearing"
				jv.user_remark = "Cheque/Giro Clearing: " + bank_account + ", Ref No: " + d.payment_entry
				jv.clearance_date = d.clearance_date

				jv.append("accounts",{
						"account": bank_account,
						"account_description": "Cheque/Giro Clearing against " + d.payment_entry,	
						"debit_in_account_currency": debit_amount,
						"credit_in_account_currency": credit_amount
					})
					
				jv.append("accounts",{
						"account": d.clearance_account,
						"account_description": "Cheque/Giro Clearing against " + d.payment_entry,	
						"debit_in_account_currency": credit_amount,
						"credit_in_account_currency": debit_amount
					})

				jv.insert()
				jv.submit()
				#frappe.msgprint("Clearance Date : " + cstr(d.clearance_date))
				frappe.db.sql("""update `tab{0}` set clearance_date = %s where name=%s""".format(jv.doctype), 
				(d.clearance_date, jv.name))

				frappe.db.commit()
				#frappe.msgprint("Successfully generated clearing journal voucher: " + jv.name)
		#else:
		#	frappe.throw(_("Cheque number is required. Also please set Clearance Date and Clearing Account"))
		#	return
		if msg:
			frappe.msgprint(msg)
