# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt
from __future__ import unicode_literals

import json
import frappe
import frappe.handler
import frappe.client
from frappe.utils.response import build_response
from frappe import _
from six.moves.urllib.parse import urlparse, urlencode
from six import string_types
import base64
from frappe.utils import get_datetime, cstr, flt, format_datetime
import datetime

def handle():
	"""
	Handler for `/api` methods

	### Examples:

	`/api/method/{methodname}` will call a whitelisted method

	`/api/resource/{doctype}` will query a table
		examples:
		- `?fields=["name", "owner"]`
		- `?filters=[["Task", "name", "like", "%005"]]`
		- `?limit_start=0`
		- `?limit_page_length=20`

	`/api/resource/{doctype}/{name}` will point to a resource
		`GET` will return doclist
		`POST` will insert
		`PUT` will update
		`DELETE` will delete

	`/api/resource/{doctype}/{name}?run_method={method}` will run a whitelisted controller method
	"""

	validate_oauth()
	validate_auth_via_api_keys()

	parts = frappe.request.path[1:].split("/",3)
	call = doctype = name = None

	if len(parts) > 1:
		call = parts[1]

	if len(parts) > 2:
		doctype = parts[2]

	if len(parts) > 3:
		name = parts[3]

	if call=="method":
		frappe.local.form_dict.cmd = doctype
		return frappe.handler.handle()

	elif call=="resource":
		if "run_method" in frappe.local.form_dict:
			method = frappe.local.form_dict.pop("run_method")
			doc = frappe.get_doc(doctype, name)
			doc.is_whitelisted(method)

			if frappe.local.request.method=="GET":
				if not doc.has_permission("read"):
					frappe.throw(_("Not permitted"), frappe.PermissionError)
				frappe.local.response.update({"data": doc.run_method(method, **frappe.local.form_dict)})

			if frappe.local.request.method=="POST":
				if not doc.has_permission("write"):
					frappe.throw(_("Not permitted"), frappe.PermissionError)

				frappe.local.response.update({"data": doc.run_method(method, **frappe.local.form_dict)})
				frappe.db.commit()

		else:
			if name:
				if frappe.local.request.method=="GET":
					doc = frappe.get_doc(doctype, name)
					if not doc.has_permission("read"):
						raise frappe.PermissionError
					frappe.local.response.update({"data": doc})

				if frappe.local.request.method=="PUT":
					data = get_request_form_data()

					doc = frappe.get_doc(doctype, name)

					if "flags" in data:
						del data["flags"]

					# Not checking permissions here because it's checked in doc.save
					doc.update(data)

					frappe.local.response.update({
						"data": doc.save().as_dict()
					})

					if doc.parenttype and doc.parent:
						frappe.get_doc(doc.parenttype, doc.parent).save()

					frappe.db.commit()

				if frappe.local.request.method=="DELETE":
					# Not checking permissions here because it's checked in delete_doc
					frappe.delete_doc(doctype, name, ignore_missing=False)
					frappe.local.response.http_status_code = 202
					frappe.local.response.message = "ok"
					frappe.db.commit()


			elif doctype:
				if frappe.local.request.method=="GET":
					if frappe.local.form_dict.get('fields'):
						frappe.local.form_dict['fields'] = json.loads(frappe.local.form_dict['fields'])
					frappe.local.form_dict.setdefault('limit_page_length', 20)
					frappe.local.response.update({
						"data":  frappe.call(frappe.client.get_list,
							doctype, **frappe.local.form_dict)})

				if frappe.local.request.method == "POST":
					data = get_request_form_data()
					data.update({
						"doctype": doctype
					})

					err_flag = 0
					body = data or {}
					if doctype == "FeeBill" and body:
						data = {}
						for k,v in body.items():
							data[k.lower()] = v
							if not v and k != "AdditionalData": err_flag = 1

						try:
							data.update({
								"transactiondate": datetime.datetime.strptime(data.get("transactiondate"),"%d/%m/%Y %H:%M:%S"), #get_datetime(data["transactiondate"]),
								"totalamount": flt(frappe.get_value("Fees",{"name":data.get("companycode") + data.get("customernumber")},"outstanding_amount")) or 0,
								"minimumpayment": flt(frappe.get_value("Fees",{"name":data.get("companycode") + data.get("customernumber")},"minimum_payment")) or 0,
								"customername": frappe.get_value("Fees",{"name":data.get("companycode") + data.get("customernumber")},"student_name")
							})
						except Exception as e:
							err_flag = 1
							error_trace = frappe.get_traceback()
							if error_trace: frappe.log_error(error_trace)

						feebill = {}
						if not data.get("totalamount") or not data.get("customername"): err_flag = 1
						elif frappe.db.exists(doctype,{"name":data.get("requestid")}):
							err_flag = 1
							#raise frappe.ValidationError("Duplicate RequestID. Rejected")	

						if not err_flag:
							try:
								feebill = frappe.get_doc(data).insert().as_dict()
							except Exception as e:
								err_flag = 1
								error_trace = frappe.get_traceback()
								if error_trace: frappe.log_error(error_trace)
						
						#if frappe.get_value("Fees",{"name":data.get("companycode") + data.get("customernumber")},"outstanding_amount") and \
						#	not frappe.db.exists(doctype,{"name":data.get("requestid")}) and not err_flag:

						if not err_flag:
							#feebill = frappe.get_doc(data).insert().as_dict()

							for k,v in json.loads(feebill.response_format).items():
								frappe.local.response.update({
									k: feebill.get(k.lower()) or ""
								})

							minimum_payment = "MinimumPayment " + '%0.2f' % flt(feebill.get("minimumpayment")) or "0.00"

							frappe.local.response.update({
								"InquiryReason": json.loads(feebill.get("inquiryreason")) or [],
								"FreeTexts": {"Indonesian": minimum_payment, "English": minimum_payment}, #json.loads(feebill.get("freetexts")) or [],
								"DetailBills": [],
								"TotalAmount": '%0.2f' % flt(feebill.get("totalamount")) or "0.00",
								"AdditionalData": ""
							})

						else:
							feebill = frappe.db.sql("""select response_format from `tabFeeBill` order by creation desc limit 1""", as_dict=1)
							if feebill:
								for k,v in json.loads(feebill[0].response_format).items():
									frappe.local.response.update({
										k: v
									})

							del body["doctype"]
							del body["TransactionDate"]
							del body["ChannelType"]
							for k,v in body.items():
								frappe.local.response.update({
									k: v
								})
							frappe.local.response.update({
								"InquiryStatus": "01",
								"CustomerName": data.get("customername") or "",
								"TotalAmount": "0.00",
								"InquiryReason": {"Indonesian":"Gagal","English":"Failed"},
								"AdditionalData": ""
							})
							data["inquirystatus"] = "01"

							if not frappe.db.exists(doctype,{"name":data.get("requestid")}) and not err_flag:
								frappe.get_doc(data).insert()
							#raise frappe.DoesNotExistError

					elif doctype == "FeePayment" and body:
						data = {}
						for k,v in body.items():
							data[k.lower()] = v
							if not v and k != "AdditionalData": err_flag = 1
							elif k == "FlagAdvice" and v not in ("Y","N"): err_flag = 1

						try:
							data.update({
								"transactiondate": datetime.datetime.strptime(data.get("transactiondate"),"%d/%m/%Y %H:%M:%S"), #get_datetime(data["transactiondate"]),
								"parenttype": "Fees",
								"parentfield": "payments",
								"parent": frappe.get_value("Fees",{"name":data.get("companycode") + data.get("customernumber")},"name") or "",
								"detailbills": cstr(data.get("detailbills")),
								"customername": frappe.get_value("Fees",{"name":data.get("companycode") + data.get("customernumber")},"student_name") or ""
							})
						except Exception as e:
							err_flag = 1
							error_trace = frappe.get_traceback()
							if error_trace: frappe.log_error(error_trace)


						if data.get("parent") and not err_flag:
							idx = frappe.db.sql("""select idx from `tabFeePayment` where parent=%s order by idx desc limit 1""", (data.get("parent")),as_dict=0) or 0.0
							if idx: idx = flt(idx[0][0])
							data.update({
								"idx": flt(idx) + 1
							})

							fees = {}
							try:
								fees = frappe.get_doc(data).insert().as_dict()
							except Exception as e:
								err_flag = 1
								error_trace = frappe.get_traceback()
								if error_trace: frappe.log_error(error_trace)

							if not err_flag:
								for k,v in json.loads(fees.response_format).items():
									frappe.local.response.update({
										k: fees.get(k.lower()) or ""
									})
							
								frappe.local.response.update({
									"PaymentFlagReason": json.loads(fees.get("paymentflagreason")) or [],
									"FreeTexts": json.loads(fees.get("freetexts")) or [],
									"DetailBills": [],
									"TotalAmount": '%0.2f' % flt(fees.get("totalamount")) or "0.00",
									"PaidAmount": '%0.2f' % flt(fees.get("paidamount")) or "0.00",
									"TransactionDate": body.get("TransactionDate"),
									"AdditionalData": ""
								})
							
						if err_flag:
							#raise frappe.DoesNotExistError							
							del body["doctype"]
							del body["ChannelType"]
							del body["Reference"]
							del body["FlagAdvice"]
							if body.get("SubCompany"): del body["SubCompany"]

							for k,v in body.items():
								frappe.local.response.update({
									k: v
								})
							frappe.local.response.update({
								"PaymentFlagStatus": "01",
								"PaymentFlagReason": {"Indonesian":"Gagal","English":"Failed"},
								"FreeTexts": [{"Indonesian":"","English":""}],
								"DetailBills": [],
								"AdditionalData": ""
							})
							
					else:
						frappe.local.response.update({
							"data": frappe.get_doc(data).insert().as_dict()
						})

					frappe.db.commit()
			else:
				raise frappe.DoesNotExistError

	else:
		raise frappe.DoesNotExistError

	return build_response("json")

def get_request_form_data():
	if frappe.local.form_dict.data is None:
		data = json.loads(frappe.safe_decode(frappe.local.request.get_data()))
	else:
		data = frappe.local.form_dict.data
		if isinstance(data, string_types):
			data = json.loads(frappe.local.form_dict.data)

	return data

def validate_oauth():
	from frappe.oauth import get_url_delimiter
	form_dict = frappe.local.form_dict
	authorization_header = frappe.get_request_header("Authorization").split(" ") if frappe.get_request_header("Authorization") else None
	if authorization_header and authorization_header[0].lower() == "bearer":
		from frappe.integrations.oauth2 import get_oauth_server
		token = authorization_header[1]
		r = frappe.request
		parsed_url = urlparse(r.url)
		access_token = { "access_token": token}
		uri = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path + "?" + urlencode(access_token)
		http_method = r.method
		body = r.get_data()
		headers = r.headers

		required_scopes = frappe.db.get_value("OAuth Bearer Token", token, "scopes").split(get_url_delimiter())

		valid, oauthlib_request = get_oauth_server().verify_request(uri, http_method, body, headers, required_scopes)

		if valid:
			frappe.set_user(frappe.db.get_value("OAuth Bearer Token", token, "user"))
			frappe.local.form_dict = form_dict


def validate_auth_via_api_keys():
	"""
	authentication using api key and api secret

	set user
	"""
	try:
		authorization_header = frappe.get_request_header("Authorization", None).split(" ") if frappe.get_request_header("Authorization") else None
		if authorization_header and authorization_header[0] == 'Basic':
			token = frappe.safe_decode(base64.b64decode(authorization_header[1])).split(":")
			validate_api_key_secret(token[0], token[1])
		elif authorization_header and authorization_header[0] == 'token':
			token = authorization_header[1].split(":")
			validate_api_key_secret(token[0], token[1])
	except Exception as e:
		raise e

def validate_api_key_secret(api_key, api_secret):
	user = frappe.db.get_value(
		doctype="User",
		filters={"api_key": api_key},
		fieldname=['name']
	)
	form_dict = frappe.local.form_dict
	user_secret = frappe.utils.password.get_decrypted_password ("User", user, fieldname='api_secret')
	if api_secret == user_secret:
		frappe.set_user(user)
		frappe.local.form_dict = form_dict
