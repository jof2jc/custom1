# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class BillingReceipt(Document):
	pass


def update_billing_receipt_on_invoice(self, method):
	if self.docstatus > 0:
		for d in self.references:
			if "billing_receipt_no" in frappe.db.get_table_columns(d.reference_doctype):
				inv = frappe.get_doc(d.reference_doctype, d.reference_name)

				if self.docstatus == 1 and not inv.billing_receipt_no:
					inv.db_set("billing_receipt_no", d.parent)
					frappe.db.commit()
				elif self.docstatus == 2 and inv.billing_receipt_no:
					inv.db_set("billing_receipt_no", "")
					frappe.db.commit()
				
					