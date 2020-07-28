# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import hmac, hashlib, requests, json, datetime
from frappe.utils import get_datetime, convert_utc_to_user_timezone, cstr

class VEFAPIIntegration(Document):
	pass

	def test_api_request(self):
		if not self.url or not self.method:
			frappe.msgprint("Please specify url path and method")
			return
		elif not self.headers:
			frappe.msgprint("Please specify Headers")
			return

		#access_token = generate_access_token()
		#signature = generate_signature(self.url, 'GET', access_token, self.body or '')
		#timestamp = convert_utc_to_user_timezone(datetime.datetime.utcnow()).isoformat(timespec='milliseconds')

		#frappe.msgprint('signature = ' + signature)
		headers=None
		if not self.is_json:
			data = self.body
		else: data = json.loads(self.body)

		headers = json.loads(self.headers)
		#headers={'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json', 'X-BCA-Key': self.api_key, 'X-BCA-Timestamp':timestamp, 'X-BCA-Signature': signature}

		if self.method == "POST":
			result = requests.post(self.main_url + self.url,headers=headers, data=data).content
		elif self.method == "GET": 
			result = requests.get(self.main_url + self.url,headers=headers, data=data).content

		#frappe.msgprint('result = ' + str(result))
		self.result = cstr(json.loads(result))


@frappe.whitelist()
def generate_access_token(docname):
	'''obtain access_token'''
	api_doc = frappe.get_doc("VEF API Integration",docname)
	result = {}

	if api_doc.provider_type == 'Bank' and api_doc.provider_name == 'BCA':
		token_headers={'Authorization': api_doc.basic_base_64_encoded,'Content-Type': 'application/x-www-form-urlencoded'}
		token_data={'grant_type':'client_credentials'}

		result = json.loads(requests.post(api_doc.main_url + '/api/oauth/token',headers=token_headers,data=token_data).content) or frappe._dict()

	return result.get("access_token") or ""


@frappe.whitelist()
def generate_signature(docname, url_path, method, access_token='', BodyString='', timestamp=''):
	'''generate signature'''
	api_doc = frappe.get_doc("VEF API Integration",docname)
	signature = ""

	if api_doc.provider_type == 'Bank' and api_doc.provider_name == 'BCA':
		if not access_token:
			access_token = api_doc.access_token

		body = hashlib.sha256(BodyString.encode('utf-8')).hexdigest()
		api_secret = api_doc.api_secret.encode('utf-8')

		if not timestamp:
			timestamp = convert_utc_to_user_timezone(datetime.datetime.utcnow()).isoformat(timespec='milliseconds')

		StringToSign = method + ':' + url_path + ':' + access_token + ':' + body.lower() + ':' + timestamp

		signature = hmac.new(api_secret, StringToSign.encode('utf-8'), hashlib.sha256).hexdigest()

	elif api_doc.provider_type == 'Marketplace' and api_doc.provider_name == 'Shopee':
		api_secret = api_doc.api_key.encode('utf-8')

		StringToSign = api_doc.main_url + url_path + '|' + BodyString

		signature = hmac.new(api_secret, StringToSign.encode('utf-8'), hashlib.sha256).hexdigest()

	return signature or ""
