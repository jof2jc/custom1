from __future__ import unicode_literals
import frappe
from frappe import _

def get_data():
	return [
		{
			"module_name": "Custom1",
			"category": "Modules",
			"label": _("My Reports"),
			"color": "#3498db",
			"icon": "octicon octicon-repo",
			"type": "module",
			"description": "Custom1"
		},
		{
			"module_name": "Marketplace Flow",
			"category": "Modules",
			"label": _("Marketplace Flow"),
			"color": "#3498db",
			"icon": "fa fa-truck",
			"type": "module",
			"description": "Operation workflow from online order to pick-pack-delivery"
		},
		{
			"module_name": "My System Settings",
			"category": "Modules",
			"label": _("My System Settings"),
			"color": "#bdc3c7",
			"icon": "octicon octicon-settings",
			"type": "module"
		},      
	]
