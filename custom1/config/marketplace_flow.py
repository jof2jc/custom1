from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Item Operation"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "Data Import",
					"label": _("Import Online Order"),
					"onboard": 1
				},
				{
					"type": "report",
					"name": "Order Invoice Sheet",
					"doctype": "Sales Invoice",
					"onboard": 1
				},
				{
					"type": "doctype",
					"name": "Pick Item",
					"label": _("Pick Item to pack"),
					"onboard": 1,
					"description": _("Pick Item per order")
				},
				{
					"type": "doctype",
					"name": "Pick and Pack",
					"label": _("Scan-out To Deliver Items"),
					"onboard": 1
				}
			]
		},
		{
			"label": _("Stock"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "BOM"
				},
				{
					"type": "doctype",
					"name": "Item",
					"label": _("Item List"),
					"onboard": 1,
				}
			]
		}
	]