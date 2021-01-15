# -*- coding: utf-8 -*-
# Copyright (c) 2020, jonathan and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import hmac, hashlib, requests, json, datetime
from frappe.utils import get_datetime, getdate, nowdate, convert_utc_to_user_timezone, cstr, cint, flt, now_datetime, add_to_date, add_days
from six import string_types
from frappe.api import get_request_form_data
import lazop, datetime


@frappe.whitelist(allow_guest = True)
def ping2():
	data = get_request_form_data()
	data.update({"test_rpc":"1"})
	return data

@frappe.whitelist(allow_guest = True)
def get_push_data_from_marketplace():
	authorization_header = frappe.get_request_header("Authorization") if frappe.get_request_header("Authorization") else ""
	data = get_request_form_data()

	if data:
		if data.get("shop_id") and data.get("code"): #Shopee
			#api_doc = frappe.get_doc("Customer",{"shop_id":data.get("shop_id")})
			if frappe.db.exists("Customer",{"shop_id":data.get("shop_id")}) and data.get("code"):
				for d in data.get("data"):
					if frappe.db.exists("Sales Order",{"name":data.get("ordersn"),"docstatus":1}):
						so = frappe.get_doc("Sales Order", data.get("ordersn"))

						if data.get("code") == "3": #update order_status
							so.db_set("order_status", data.get("status"))							
							#frappe.set_value("Sales Order", data.get("ordersn"), "order_status", data.get("status"))
						elif data.get("code") == "4": #update tracking_no
							so.db_set("awb_no", data.get("trackingno"))
							#frappe.set_value("Sales Order", data.get("ordersn"), "awb_no", data.get("trackingno"))

						frappe.db.commit()
						auto_create_sales_invoice_based_on_sales_order_update(so)
	
	else: 
		error_trace = frappe.get_traceback()
		if error_trace: 
			frappe.log_error(error_trace)
		else: frappe.log_error("Unauthorized request")

	return ""
	

def auto_create_sales_invoice_based_on_sales_order_update(self):
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

	if "awb_no" in frappe.db.get_table_columns(self.doctype) and self.docstatus == 1:
		if len(cstr(self.awb_no)) > 7:
			if not frappe.get_list("Sales Invoice Item",fields=["name"],filters=[["parent","=",self.name],["docstatus","<=","1"]]):
				inv = make_sales_invoice(self.name, ignore_permissions=True)
				inv.pending_remarks = self.order_status
				inv.order_status = "SUDAH DIPROSES"
				inv.package_weight = inv.total_net_weight
				try:
					inv.insert()
					frappe.db.commit()
				except Exception as e:
					error_trace = frappe.get_traceback()
					if error_trace: 
						frappe.log_error(error_trace)

		update_so_based_on_order_status(self)

def update_so_based_on_order_status(so, order_items_data=None):
	if order_items_data:
		for item in order_items_data:
			so.db_set("order_status", item.get('status'))
			so.db_set("awb_no", item.get('tracking_code'))
			so.db_set("courier", item.get('shipment_provider'))
			break

	if not so.get("order_status"): return

	if ("CANCEL" in so.order_status.upper()) or ("BATAL" in so.order_status.upper()) or ("FAILED" in so.order_status.upper()):
		try:
			so.cancel()

		except Exception as e:
			error_trace = frappe.get_traceback()
			if error_trace: 
				frappe.log_error(error_trace)
	frappe.db.commit()
	print("Updated %s data= %s, %s" % (so.name, so.order_status, so.awb_no))

def update_stock_for_marketplace_item(self, method):
	for shop in frappe.get_list("Customer",fields=["name"],filters=[["is_marketplace_shop","=",1],["api_key","!=",""]]):
		api_doc = frappe.get_doc("Customer", shop.name)

		if not api_doc: continue
	
		item = self
		if item.warehouse != api_doc.marketplace_warehouse: continue

		for r in api_doc.get('api_end_point',{'disabled':0,'type':'Update Stock'}):
			headers = json.loads(r.header.strip())
			body = {} 

			if headers and r.body:
				for k,v in json.loads(r.body.strip()).items():
					body.update({k:eval(v)})

			if r.end_point and body:
				signature = generate_signature(api_doc, r.end_point, r.method, BodyString=json.dumps(body))
				headers["Authorization"] = signature

			if body.get("item_id") or body.get("variation_id"):
				try:
					result = make_api_request(r.end_point, r.method, headers, json.dumps(body))
				except Exception as e:
					err_flag = 1
					error_trace = frappe.get_traceback()
					if error_trace: 
						frappe.log_error(error_trace)
			


def insert_new_sales_order(api_doc, d, order_items_data, r):
	order_id = d.get("ordersn") or d.get("order_id")
	if frappe.db.exists("Sales Order",{"name": order_id}): 
		if d.get("order_id"): #lazada, check for order update
			'''
			val = frappe.db.get_values("Sales Order", {"name":d.get("order_id"),"docstatus":1}, ["awb_no","order_status"])
			if val:
				frappe.db.set_value("Sales Order",d.get("order_id"),{
					"awb_no": d.get("tracking_code") if val[0][0] != d.get("tracking_code") else val[0][0],
					"order_status": d.get("status") if val[0][1] != d.get("status") else val[0][1]
				})
			'''
			update_so_based_on_order_status(frappe.get_doc("Sales Order",{"name":d.get("order_id")}), order_items_data)
		print("%s exists. Skip inserting new order" % (d.get("ordersn") or d.get("order_id")))
		return
	

	order_detail_json = json.loads(r.order_detail_json.strip())
	order_item_json = json.loads(r.order_item_json.strip())
	order = {}
	
	order.update({"doctype":"Sales Order","order_type":"Sales"})

	if order_detail_json:
		for k,v in order_detail_json.items():
			order.update({k:eval(v)})

	so = frappe.get_doc(order)
	#print(so.no_online_order, so.name)

	for item in order_items_data: #populate order items
		so_item = {}
		item_code = frappe.get_value("Item",{"item_code":item.get("sku")},"item_code") or \
				frappe.get_value("Item",{"item_code":item.get("shop_sku")},"item_code") or \
				frappe.get_value("Marketplace Items",{"marketplace_store":api_doc.name,"variant_id":item.get("variation_id")},"parent") or \
				frappe.get_value("Marketplace Items",{"marketplace_store":api_doc.name,"item_id":item.get("item_id")},"parent") or ""

		if not item_code:
			item_code = frappe.db.sql('''select item_code from `tabItem` where disabled=0 and item_code=%s limit 1''', (item.get("sku")), as_dict=0) or \
				frappe.db.sql('''select item_code from `tabItem` where disabled=0 and 
				(item_name like %s or description like %s) limit 1''', 
				(("%" + item.get("sku") + "%"),("%" + item.get("sku") + "%")), as_dict=0)
			if item_code: item_code = item_code[0][0]

		if so and order_item_json:
			for idx, r in enumerate(order_item_json):
				if idx == 0: #update parent order if it consists in child data
					for k,v in r.items():
						so.update({k:eval(v)})

				else:
					for k,v in r.items():
						if k != "doctype": so_item.update({k:eval(v)})
						else: so_item.update({k:v})

						so_item.update({
							"delivery_date":so.get("delivery_date"), 
							"warehouse": frappe.get_value("Customer",api_doc.name,"marketplace_warehouse") or \
									frappe.db.get_single_value("Stock Settings","default_warehouse")
						})	

		so.append("items",so_item)

	if not so.get("order_status"): return #order_status is mandatory

	if ("CANCEL" in so.order_status.upper()) or ("BATAL" in so.order_status.upper()):
		so.update({"docstatus":0})
	else: so.update({"docstatus":1})
					
	print(so, " docstatus: ", so.get("docstatus"))
	try:
		so.insert()
		frappe.db.commit()
	except Exception as e:
		err_flag = 1
		error_trace = frappe.get_traceback()
		if error_trace: 
			frappe.log_error(error_trace)
	

def get_lazada_response(t, api_doc, access_token='', d=None):
	r = t
	client = request = response = created_before = None

	headers = json.loads(r.header.strip())
	client = eval(headers.get("client"))
	request = eval(headers.get("request"))	
	created_before = eval(headers.get("created_before")) if headers.get("created_before") and access_token else None

	#print("created_before ", created_before)

	for k,v in headers.items():
		if "param" in k: eval(v)
		#else: k = eval(v)

	if client and request:
		response = client.execute(request, access_token) if access_token else client.execute(request)

	#if access_token and r.type=="Get Order List":
	#	print(r.type, "ResponseBody==", response.body)

	return response

def make_api_request(url, method, headers, body):
	result = requests.request(method, url,headers=headers, data=body).content
	#print(cstr(json.loads(result)))
	if result:
		return json.loads(result)
	else: return {}

def run_get_marketplace_order_list():
	shop_list = frappe.get_list("Customer",fields=["name"],filters=[["is_marketplace_shop","=",1],["api_key","!=",""], ["run_order_job","=","1"]])

	if not shop_list: return

	for shop in shop_list:
		api_doc = frappe.get_doc("Customer", shop.name)

		order_list = {}
		result = {}
		order_detail_json = order_item_json = None
		if api_doc and api_doc.get("marketplace_type") and api_doc.get("api_end_point"):			
			for r in api_doc.get("api_end_point",{"disabled":0,"type":("in",["Get Order List","Get Order Detail"])}):
				if api_doc.marketplace_type == "Shopee" and api_doc.shop_id and api_doc.partner_id:
					headers = json.loads(r.header.strip())
					body = {} 

					for k,v in json.loads(r.body.strip()).items():
						body.update({k:eval(v)})				
					'''
					body.update({
						"partner_id": cint(api_doc.partner_id),
						"shopid": cint(api_doc.shop_id),
						"timestamp": cint(datetime.datetime.utcnow().replace(microsecond=0).timestamp()),
						"order_status":"ALL",
						"create_time_from":cint(add_to_date(now_datetime(),minutes=-30,as_datetime=True).replace(microsecond=0).timestamp()),
						"create_time_to":cint(now_datetime().replace(microsecond=0).timestamp())
					})
					'''
					#print(cstr(body))

					if headers:
						if r.type == "Get Order List":
							signature = generate_signature(api_doc, r.end_point, r.method, BodyString=json.dumps(body))
							headers["Authorization"] = signature

							order_list = make_api_request(r.end_point, r.method, headers, json.dumps(body))

						elif r.type == "Get Order Detail" and order_list:
							ordersn_list = []

							if order_list.get("orders"):
								for d in order_list.get("orders"):
									ordersn_list.append(d.get("ordersn"))
							
							if ordersn_list:
								body.update({
									"ordersn_list":ordersn_list
								})

								signature = generate_signature(api_doc, r.end_point, r.method, BodyString=json.dumps(body))
								headers["Authorization"] = signature
						
								'''
								if r.order_detail_json:
									order_detail_json = json.loads(r.order_detail_json.strip())

								if r.order_item_json:
									order_item_json = json.loads(r.order_item_json.strip())
								'''

								result = make_api_request(r.end_point, r.method, headers, json.dumps(body))

							if result.get("orders"): 
								for d in result.get("orders"):
									print("Shopee ", d.get("ordersn"), d.get("create_time"), d.get("update_time"))
									order_items_data = d.get("items")
									insert_new_sales_order(api_doc, d, order_items_data, r)

					else:
						return "Headers Error"

				elif api_doc.marketplace_type == "Lazada":
					access_token = ""
					for t in api_doc.get("api_end_point",{"disabled":0,"type":("in",["Refresh Token"])}):
						response = get_lazada_response(t, api_doc, access_token='')
						access_token = response.body.get("access_token") or ""
						
						if access_token:
							frappe.db.set_value(t.doctype, t.name, {
								"access_token":access_token,
								"refresh_token":response.body.get("refresh_token") or ""
							})
							frappe.db.commit()

					if r.type == "Get Order List" and access_token:
						response = get_lazada_response(r, api_doc, access_token)

						if response.body.get("data"):
							order_list = response.body.get("data").get("orders")	#array list of orders			

					elif r.type == "Get Order Detail" and order_list and access_token:
						for d in order_list:
							#if frappe.db.exists("Sales Order",{"name":d.get("order_id")}): 
							#	continue
							print("Lazada ", d.get("order_id"), d.get("created_at"), d.get("updated_at"))
							response = get_lazada_response(r, api_doc, access_token, d)

							if response.body.get("data"):
								order_items_data = response.body.get("data")
								insert_new_sales_order(api_doc, d, order_items_data, r)


			''' Insert orders result in Sales Order 
			if result.get("orders") and api_doc.marketplace_type == "Shopee": 
				for d in result.get("orders"):

					if "RETUR" in d.get("order_status").upper(): continue #skip if this is return order

					if frappe.db.exists("Sales Order",{"name":d.get("ordersn")}) or \
						frappe.db.exists("Sales Order",{"no_online_order":d.get("ordersn")}): 
						print("order %s exists. Skip" % (d.get("ordersn")))
						frappe.log_error("Order %s exists. Skip" % (d.get("ordersn")))
						continue

					#order_date = getdate(datetime.datetime.utcfromtimestamp(d.get("create_time")).strftime('%Y-%m-%d %H:%M:%S'))
					#delivery_date = add_days(nowdate(), days=3)

					order = {}
					order.update({"doctype":"Sales Order","order_type":"Sales"})
					if order_detail_json:
						for k,v in order_detail_json.items():
							order.update({k:eval(v)})

					so = frappe.get_doc(order)
					#print(cstr(order.get('items')))

					for item in d.get("items"):
						so_item = {}
						item_code = frappe.get_value("Item",{"item_code":item.get("item_sku")},"item_code") or \
								frappe.get_value("Marketplace Items",{"marketplace_store":api_doc.name,"variant_id":item.get("variation_id")},"parent") or \
								frappe.get_value("Marketplace Items",{"marketplace_store":api_doc.name,"item_id":item.get("item_id")},"parent") or ""

						if order:
							for r in order_item_json:
								for k,v in r.items():
									#print(k + '= %s' % (v))
									if k != "doctype": so_item.update({k:eval(v)})
									else: so_item.update({k:v})
									so_item.update({
										"delivery_date":so.get("delivery_date"), 
										"warehouse": frappe.get_value("Customer",api_doc.name,"marketplace_warehouse") or \
												frappe.db.get_single_value("Stock Settings","default_warehouse")
									})

						so.append("items",so_item)

					if "CANCEL" or "BATAL" in so.order_status.upper():
						so.update({"docstatus":0})
					else: so.update({"docstatus":1})

					#so.insert()
					
					try:
						so.insert()
					except Exception as e:
						err_flag = 1
						error_trace = frappe.get_traceback()
						if error_trace: 
							frappe.log_error(error_trace)
			'''		


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
def generate_signature(api_doc, url, method, access_token='', BodyString='', timestamp=''):
	signature = ""

	#timestamp = convert_utc_to_user_timezone(datetime.datetime.utcnow()).isoformat(timespec='milliseconds')

	if api_doc.marketplace_type == 'Shopee':
		api_secret = api_doc.api_key.encode('utf-8')

		StringToSign = url + '|' + BodyString

		signature = hmac.new(api_secret, StringToSign.encode('utf-8'), hashlib.sha256).hexdigest()

	return signature or ""

@frappe.whitelist()
def get_shop_authorization_token(marketplace, redirect_url, partner_key):
	token = ""
	if marketplace == "Shopee":
		base_string = partner_key + redirect_url
		token = hashlib.sha256(base_string.encode('utf-8')).hexdigest()

	return token

def verify_push_msg(url, request_body, partner_key, authorization=''):
	base_string = url + '|' + request_body
	
	cal_auth = hmac.new(partner_key, base_string.encode('utf-8'), hashlib.sha256).hexdigest()

	if cal_auth != authorization:
		return False
	else:
		return True
