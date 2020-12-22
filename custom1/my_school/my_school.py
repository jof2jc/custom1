from __future__ import unicode_literals
import frappe
from frappe import _, scrub
from frappe.utils.user import add_role


def auto_create_user(self,method):
	user_name = ""
	role_profile = ""
	user_doc = None
	if self.doctype == "Guardian":
		user_name = self.guardian_name
	else:
		user_name = self.instructor_name
		
	if not frappe.get_value("User",{"name": self.email_address},"name") and self.email_address:
		user_doc = frappe.get_doc({"doctype":"User","email":self.email_address,"username":self.email_address,
			"first_name": user_name, "enabled": 1, "send_welcome_email": 0})
		user_doc.new_password = b'123456' #default_password
		user_doc.flags.ignore_permissions = True
		user_doc.insert()
		add_role(user_doc.name, self.doctype)
		#user_doc.save()
		self.user = user_doc.name
		frappe.db.commit()

	elif frappe.get_value("User", {"name": self.email_address},"name"):
		user_doc = frappe.get_doc("User", self.email_address)
		if not self.user: self.user = user_doc.name
		if user_doc:	
			if user_doc.role_profile_name:
				user_doc.role_profile_name = ""
				user_doc.save()
			add_role(user_doc.name, self.doctype)
			frappe.db.commit()