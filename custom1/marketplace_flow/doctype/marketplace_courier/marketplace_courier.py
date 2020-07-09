# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.user import is_website_user

class MarketplaceCourier(Document):
	pass

def has_website_permission(doc, ptype, user, verbose=False):
	return True

def get_courier_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by="modified"):
	#frappe.throw("custom list MP Courier: " + str(doctype), frappe.PermissionError)

	from frappe.www.list import get_list

	user = frappe.session.user
	student = frappe.db.get_value('Student', {'student_email_id': user}, 'name')

	ignore_permissions = False
	doctype = "Payment Entry"
	if is_website_user() and student:
		if not filters: filters = {}

		filters["docstatus"] = 1

		if student:
			filters["party_type"] = "Student"
			filters["party"] = student

		ignore_permissions = True

	return get_list(doctype, txt, filters, limit_start, limit_page_length, ignore_permissions=ignore_permissions)

def get_list_context(context=None):
	return {
		"show_sidebar": True,
		"show_search": True,
		"no_breadcrumbs": True,
		"title":"Payment History",
		"get_list": get_courier_list,
		#"allow_guest": True,
		"row_template": "templates/includes/courier/courier_row.html"
	}