import frappe

@frappe.whitelist()
def switch_theme(theme):
	if theme in ["Dark", "Light", "Automatic", "Intellore-theme","Forest-Theme-1","Business-Theme","Intellore-Theme-1"]:
		frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)

# import frappe

# @frappe.whitelist()
# def switch_theme(theme):
# 	if theme in ["Dark", "Light", "Automatic", "Intellore-theme"]:
# 		frappe.db.set_value("User", frappe.session.user, "desk_theme", theme)