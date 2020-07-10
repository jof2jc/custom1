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
					"name": "Data Import Legacy",
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
					"name": "Sales Invoice",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Purchase Invoice",
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
					"name": "Journal Entry",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Pick and Pack",
					"label": _("Scan to Deliver Items (Pick and Pack)"),
					"onboard": 1
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
					"label": _("Item Group"),
					"link": "Tree/Item Group",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Product Bundle",
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
					"name": "Mode of Payment",
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
				{
					"type": "doctype",
					"label": _("Warehouse"),
					"link": "Tree/Warehouse",
					"onboard": 1,
				},
			]
		},
		{
			"label": _("Working Sheet"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Task",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Marketplace CSO",
					"onboard": 1
				},
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