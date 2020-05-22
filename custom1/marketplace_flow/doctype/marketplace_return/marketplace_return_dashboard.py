from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'marketplace_return',
		'internal_links': {
			'Sales Invoice': ['items', 'sales_return_no'],
			'Purchase Invoice': ['items', 'purchase_return_no']
		},
		'transactions': [
			{
				'label': _('Transaction References'),
				'items': ['Sales Invoice', 'Purchase Invoice']
			}
		]
	}