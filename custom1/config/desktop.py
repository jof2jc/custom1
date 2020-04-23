from __future__ import unicode_literals
import frappe
from frappe import _

def get_data():
	return [
		{
			"module_name": "Custom1",
			"category": "Modules",
			"label": _("Custom1"),
			"color": "#3498db",
			"icon": "octicon octicon-repo",
			"type": "module",
			"description": "Custom1"
		}
                
	]
