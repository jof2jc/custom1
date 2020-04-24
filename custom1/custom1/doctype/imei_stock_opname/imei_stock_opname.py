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
		data1 = {}
		data2 = {}
		data3 = []
		data4 = {}
		imei=[]

		#for d in self.items:
		serial_nos = cstr(self.imei).strip().replace(',', '\n').split('\n') #list(cstr(self.imei).strip().replace(',', '\n').split('\n'))

		#print serial_nos

		self.set('invalid_imei', {}) #clear child table
		
		#for i in serial_nos:
		#	imei.append(i)

		valid_serial_nos = []
		#remove duplicates
		for val in serial_nos:
			if val:
				val = val.strip()
				if val not in valid_serial_nos:
					valid_serial_nos.append(val)

					#never exists
					if not frappe.db.exists("Serial No", val):
						self.append("invalid_imei", {
							"imei": val,
							"status":"Not Exists [-1]",
							"item_code": "",
							"warehouse": "",
							"delivery_document_no": ""
						})

	
		#sold
		data1 = frappe.db.sql("""SELECT name, 'Sold [0]' as status, item_code, warehouse, delivery_document_no FROM `tabSerial No` 
			Where ifnull(delivery_document_no,'')<>'' And ifnull(delivery_date,'')<>'' 
			And name in (%s)""" % ", ".join(["%s"] * len(valid_serial_nos)), tuple(valid_serial_nos), as_dict=1)
		#frappe.msgprint(_("data1 {0}").format(data1))

		#in other warehouse
		data2 = frappe.db.sql("""SELECT name, 'In Other Warehouse [2]' as status, item_code, warehouse, delivery_document_no FROM `tabSerial No` 
			Where ifnull(delivery_document_no,'')='' And ifnull(delivery_date,'')='' 
			And name In %s AND ifnull(warehouse,'')<>'' AND warehouse <> %s""", (tuple(valid_serial_nos), self.warehouse), as_dict=1)


		#not scanned
		data4 = frappe.db.sql("""SELECT name, item_code, warehouse FROM `tabSerial No` 
			Where ifnull(delivery_document_no,'')='' And ifnull(delivery_date,'')='' 
			And name NOT In %s AND warehouse=%s""", (tuple(valid_serial_nos), self.warehouse), as_dict=1)


		for d in data1:
			self.append("invalid_imei", {
				"imei": d.name,
				"status":d.status,
				"item_code": d.item_code,
				"warehouse": d.warehouse,
				"delivery_document_no": d.delivery_document_no
			})

		for d in data2:
			self.append("invalid_imei", {
				"imei": d.name,
				"status":d.status,
				"item_code": d.item_code,
				"warehouse": d.warehouse,
				"delivery_document_no": d.delivery_document_no
			})

		self.set('not_scanned_imei', {}) #clear child table		
		for d in data4:
			self.append("not_scanned_imei", {
				"imei": d.name,
				"item_code": d.item_code,
				"warehouse": d.warehouse
			})
		if data4:
			self.status = "Pending"	
		else:
			self.status = "Completed"

		self.imei = '\n'.join(valid_serial_nos) + '\n'

		#frappe.throw(_("Serial Nos {0}").format(data))