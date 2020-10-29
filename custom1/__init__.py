from __future__ import unicode_literals
import frappe
from frappe import _, scrub

import frappe.api
import custom1.api


frappe.api.handle = custom1.api.handle