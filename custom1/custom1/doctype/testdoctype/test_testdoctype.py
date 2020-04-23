# -*- coding: utf-8 -*-
# Copyright (c) 2015, jonathan and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest

# test_records = frappe.get_test_records('testdoctype')

class Testtestdoctype(unittest.TestCase):
	pass

@frappe.whitelist()
def mks_get_ordered_qty(item_code):
	"""Get Ordered Qty os selected item"""

	return frappe.db.sql('''select sum(it.qty) as qty from `tabSales Invoice` si, `tabSales Invoice Item` it 
		where si.name=it.parent and si.is_order=1 and si.docstatus=1 and it.delivered_qty < it.qty 
		and it.item_code=%s''', item_code, as_dict=0)
	

	
