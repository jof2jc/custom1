# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, getdate, nowdate, now_datetime, fmt_money, nowtime, cstr
from frappe import msgprint, _
from frappe.model.document import Document
import json, ast


@frappe.whitelist()
def awb_invoice(ref, awb_no, courier, sales_team, company, territory, scan_type, cancelled=0):
	if (not awb_no or not courier) and not cancelled:
		frappe.throw(_("AWB No and Courier are required"))
		return

	if (not company or not territory) and not cancelled:
		frappe.throw(_("Company or Territory not set"))
		return

	''' check if awb_no exists '''
	awb = frappe.db.get_value("AWB Invoice", awb_no.strip(), ["name","delivered"]) or ""
	
	if not awb and scan_type == "Scan Print" and not cancelled: # new scan print
		doc = frappe.new_doc("AWB Invoice")
		doc.flags.ignore_permissions = True
		
		doc.awb_no = awb_no.strip()
		doc.marketplace_courier = courier
		doc.transaction_date = now_datetime()
		doc.company = company
		doc.territory = territory
		doc.pack = 1
		doc.printed=1
		doc.sales_team = sales_team
		doc.scan_print_ref = ref

		doc.insert()
		frappe.db.commit()
		return "Scan Print Success"

	elif awb and not cancelled:
		#if not frappe.db.sql("""select name from `tabAWB Invoice` where name=%s and scan_print_ref=%s""",(awb_no.strip(), ref),as_dict=1) and not cancelled:
		#	frappe.throw(_("Scan Out Reference is not valid"))
		#	return "Scan Out Reference is not valid"

		doc = frappe.get_doc("AWB Invoice", awb_no.strip())
		doc.flags.ignore_permissions = True

		if scan_type == "Scan Out":
			doc.delivered = 1
			doc.delivery_date = now_datetime()
			doc.scan_out_ref = ref
			#doc.marketplace_courier = courier
			doc.save()
			frappe.db.commit()
			return "Scan Out Success"

		elif scan_type == "Scan Print" and doc.cancelled==1:
			doc.cancelled = 0
			doc.marketplace_courier = courier
			doc.transaction_date = now_datetime()
			doc.scan_print_ref = ref
			doc.sales_team = sales_team

			doc.save()
			frappe.db.commit()
			return "Scan Print Success"
		

	if cancelled:
		''' delete cancelled AWBs '''
		frappe.db.sql("""update `tabAWB Invoice` set cancelled=1 where scan_print_ref=%s and cancelled=0""", (ref))
		frappe.db.sql("""update `tabAWB Invoice` set delivered=0, delivery_date=null, scan_out_ref='' where scan_out_ref=%s""", (ref))

		#invoice_list = frappe.db.sql("""select name from `tabAWB Invoice` where scan_print_ref=%s""", (ref), as_dict=True)	

		#for d in invoice_list:
		#	d = frappe.get_doc("AWB Invoice", d.name)
		#	d.delete()

		frappe.db.commit()
		return "Status is cancelled and deleted"
		