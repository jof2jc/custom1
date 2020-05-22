from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Transaction"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Data Import",
					"label": _("Import Online Order"),
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Pick Item",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Pack Item",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Marketplace Outbond Receipt",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Marketplace Return",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Stock Entry",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Payment Entry",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Pick and Pack",
					"label": _("Scan-out To Deliver Items"),
					"hidden": 1
				}
			]
		},
		{
			"label": _("Setup"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Item",
					"label": _("Item List"),
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Item Group",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Customer",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Supplier",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Marketplace Courier",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Serial No",
					"onboard": 1,
					"dependencies": ["Item"],
				},
				{
					"type": "doctype",
					"name": "Batch",
					"onboard": 1,
					"dependencies": ["Item"],
				},
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "report",
					"name": "Fulfillment Sheet",
					"doctype": "Sales Invoice",
					"onboard": 1
				},
				{
					"type": "report",
					"name": "Marketplace Return Sheet",
					"doctype": "Marketplace Return",
					"onboard": 1
				},
			]
		}
	]