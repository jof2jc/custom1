from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Settings"),
			"icon": "fa fa-cog",
			"items": [
				{
					"type": "doctype",
					"name": "User Permission",
					"label": _("User Permissions"),
					"icon": "fa fa-lock",
					"description": _("Restrict user for specific document")
				},
			]
		},
	]