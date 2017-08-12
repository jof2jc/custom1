# -*- coding: utf-8 -*-
# Copyright (c) 2017, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from frappe import _
import frappe
from frappe.model.document import Document
from frappe.utils import flt, cstr, nowdate, nowtime

class IMEIStockOpname(Document):
	pass

	def validate(self):
		data={}
		#imei=['aaa','bbbb']

		#for d in self.items:
		serial_nos = list(cstr(self.imei).strip().replace(',', '\n').split('\n'))
		#for i in serial_nos:
		#	imei.append(i)

		print serial_nos
			
		data = frappe.db.sql("""SELECT name, item_code, warehouse FROM `tabSerial No` 
			Where ifnull(delivery_document_no,'')='' And ifnull(delivery_date,'')='' 
			And name NOT In %s AND warehouse=%s""", (tuple(serial_nos), self.warehouse), as_dict=1)

		print data

		self.set('not_scanned_imei', {}) #clear child table

		for d in data:
			self.append("not_scanned_imei", {
				"imei": d.name,
				"item_code": d.item_code,
				"warehouse": d.warehouse
			})
		if data:
			self.status = "Pending"	
		else:
			self.status = "Completed"

		#frappe.throw(_("Serial Nos {0}").format(data))