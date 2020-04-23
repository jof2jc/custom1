# -*- coding: utf-8 -*-
# Copyright (c) 2015, jonathan and Contributors
# See license.txt
from __future__ import unicode_literals
import frappe
from frappe import _

# test_records = frappe.get_test_records('testdoctype')

def set_vehicle_status(self, method):
	#batch_doc = frappe.get_doc("Batch", batch_id)
	#pi_doc = frappe.get_doc("Purchase Invoice", pi_name)

	#frappe.throw(_("hai {0}").format(self.name))

	if self.vehicles is not None:
		for d in self.vehicles:
			#has_batch_no = frappe.db.get_value('Item', d.item_code, 'has_batch_no')
			if d.vehicle_no:
				#frappe.throw(_("hai {0}").format(d.vehicle_no))
				vehicle_doc = frappe.get_doc("Asset", d.vehicle_no)

				if self.docstatus == 1:
					vehicle_doc.vehicle_status = "In Use"
					vehicle_doc.reference_doc_name = self.name
	
					if d.is_finish:
						#frappe.msgprint(_("hai finish"))
						vehicle_doc.vehicle_status = "Available"
						vehicle_doc.reference_doc_name = ""
				else:
					#frappe.msgprint(_("hai cancel"))
					vehicle_doc.vehicle_status = "Available"
					vehicle_doc.reference_doc_name = ""
			
				vehicle_doc.save()