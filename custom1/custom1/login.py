from __future__ import unicode_literals
import frappe
from frappe import _, scrub


def redirect_student_guardian_portal():
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = "/studentfees"