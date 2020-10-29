# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils.user import is_website_user

class FeeBill(Document):
	pass

def has_website_permission(doc, ptype, user, verbose=False):
	return True

def get_student_fees_list(doctype, txt, filters, limit_start, limit_page_length=20, order_by="modified"):
	#frappe.throw("custom list MP Courier: " + str(doctype), frappe.PermissionError)

	from frappe.www.list import get_list

	user = frappe.session.user
	guardian = frappe.db.get_value('Guardian', {'user': user}, 'name') 
	#student = frappe.db.get_value('Student', {'student_email_id': user}, 'name')

	student_list = []
	for student in frappe.get_list('Student Guardian', {'guardian': guardian}, 'parent'):
		student_list.append(student.parent)

	ignore_permissions = False
	doctype = "Fees"
	if is_website_user() and student:
		if not filters: filters = []

		#filters["docstatus"] = 1
		filters.append(["docstatus","=","1"])

		if student_list:
			#filters["student"] = student
			filters.append(["student","in",student_list])

		ignore_permissions = True

	return get_list(doctype, txt, filters, limit_start, limit_page_length, ignore_permissions=ignore_permissions)

def get_list_context(context=None):
	return {
		"show_sidebar": True,
		"show_search": True,
		"no_breadcrumbs": True,
		"title":"Payment History",
		"header":"Student Fees List",
		"get_list": get_student_fees_list,
		#"allow_guest": True,
		"row_template": "templates/includes/student_fees/student_fees_row.html"
	}