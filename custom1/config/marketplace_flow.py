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
					"name": "Pick Item",
					"onboard": 1,
					"description": _("Pick Item per order")
				}
			]
		}
	]