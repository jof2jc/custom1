from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		
		{
			"label": _("Main Reports"),
			"items": [
				{
					"type": "report",
					"name": "Batch-Wise Balance History",
					"doctype": "Batch",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Item Summary",
					"doctype": "Stock Ledger Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Stock Ledger Detail",
					"doctype": "testdoctype",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Stock Balance Summary",
					"doctype": "testdoctype",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Gross Profit",
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounts Receivable",
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounts Payable",
					"doctype": "Purchase Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Sales Register",
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Tanda Terima",
					"label": _("Tanda Terima Faktur"),
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Purchase Register",
					"doctype": "Purchase Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "General Ledger",
					"doctype": "GL Entry",
					"is_query_report": True
				}				
				
			]
		},
		{
			"label": _("Standard Reports"),
			"items": [
				
				{
					"type": "report",
					"name": "Bank Clearance Summary",
					"is_query_report": True,
					"doctype": "Journal Entry"
				},
				{
					"type": "report",
					"name": "Payment Period Based On Invoice Date",
					"is_query_report": True,
					"doctype": "Journal Entry"
				},
				{
					"type": "report",
					"name": "Delivered Items To Be Billed",
					"is_query_report": True,
					"doctype": "Sales Invoice"
				},				
				{
					"type": "report",
					"name": "Received Items To Be Billed",
					"is_query_report": True,
					"doctype": "Purchase Invoice"
				},
				
				{
					"type": "report",
					"name": "Item-wise Sales Register",
					"is_query_report": True,
					"doctype": "Sales Invoice"
				},
				{
					"type": "report",
					"name": "Item-wise Purchase Register",
					"is_query_report": True,
					"doctype": "Purchase Invoice"
				},				
				{
					"type": "report",
					"name": "Purchase Invoice Trends",
					"is_query_report": True,
					"doctype": "Purchase Invoice"
				},
				{
					"type": "report",
					"name": "Sales Invoice Trends",
					"is_query_report": True,
					"doctype": "Sales Invoice"
				},
				{
					"type": "report",
					"name": "Accounts Receivable Summary",
					"doctype": "Sales Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Accounts Payable Summary",
					"doctype": "Purchase Invoice",
					"is_query_report": True
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Customer Credit Balance",
					"doctype": "Customer"
				},
			]
		},
		{
			"label": _("Financial Reports"),
			"items": [
					
				{
					"type": "report",
					"name": "Trial Balance",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Trial Balance for Party",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Balance Sheet",
					"doctype": "GL Entry",
					"is_query_report": True
				},
				{
					"type": "report",
					"name": "Profit and Loss Statement",
					"doctype": "GL Entry",
					"is_query_report": True
				}
				                               
			]
		},
		{
			"label": _("Analytics"),
			"items": [
					
				{
					"type": "report",
					"is_query_report": True,
					"name": "Profitability Analysis",
					"doctype": "GL Entry"
				},
				{
					"type": "page",
					"name": "sales-analytics",
					"label": _("Sales Analytics"),
					"icon": "icon-bar-chart"
				},				
				{
					"type": "page",
					"name": "purchase-analytics",
					"label": _("Purchase Analytics"),
					"icon": "icon-bar-chart"
				},
 				{
					"type": "report",
					"is_query_report": True,
					"name": "Supplier-Wise Sales Analytics",
 					"label": _("Sales Analytics By Supplier"),
					"doctype": "Stock Ledger Entry"
				}
				                               
			]
		}
		
	]
