from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils.user import add_role


def auto_create_update_user(self, method):
	user_name = ""
	role_profile = ""
	user_doc = None
	if self.doctype == "Guardian":
		user_name = self.guardian_name
	else:
		user_name = self.instructor_name
		
	if not frappe.get_value("User",{"name": self.email_address},"name") and not self.user:
		user_doc = frappe.get_doc({"doctype":"User","email":self.email_address,"username":self.email_address,
			"first_name": user_name, "enabled": 1, "send_welcome_email": 0})
		user_doc.new_password = b'123456' #default_password
		user_doc.flags.ignore_permissions = True
		user_doc.insert()
		add_role(user_doc.name, self.doctype)
		#user_doc.save()
		self.user = user_doc.name
		frappe.db.commit()

def update_user_after_rename(self, force=False, merge=False, ignore_permissions=False, ignore_if_exists=False):
	if frappe.get_value("User", {"name": self.user},"name"):
		if self.name != self.email_address:
			self.db_set("email_address", self.name) #frappe.rename_doc(self.doctype, self.name, self.email_address)
		
		user_doc = None #frappe.get_doc("User", self.user)
		user = frappe.get_value("User", self.user, "name")

		if user:	
			''' rename user if email is changed '''
			new_user_name = ""
			if user != self.name:
				new_user_name = frappe.rename_doc("User", user, self.name)

			user_doc = frappe.get_doc("User", new_user_name or user)
			user_doc.db_set("username", user_doc.name)

			user_doc.db_set("role_profile_name","")

			add_role(user_doc.name, self.doctype)

			self.db_set("user",new_user_name or self.name)

			frappe.db.commit()
		
		
		#frappe.set_route("Form",self.doctype, self.email_address)