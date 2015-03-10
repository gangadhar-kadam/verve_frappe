# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint

@frappe.whitelist()
def add(doctype, name, user=None, read=1, write=0, share=0, flags=None):
	"""Share the given document with a user."""
	if not user:
		user = frappe.session.user

	share_name = frappe.db.get_value("DocShare", {"user": user, "share_name": name,
		"share_doctype": doctype})

	if share_name:
		doc = frappe.get_doc("DocShare", share_name)
	else:
		doc = frappe.new_doc("DocShare")
		doc.update({
			"user": user,
			"share_doctype": doctype,
			"share_name": name
		})

	if flags:
		doc.flags.update(flags)

	doc.update({
		# always add read, since you are adding!
		"read": 1,
		"write": cint(write),
		"share": cint(share)
	})

	doc.save(ignore_permissions=True)

	return doc

def remove(doctype, name, user, flags=None):
	share_name = frappe.db.get_value("DocShare", {"user": user, "share_name": name,
		"share_doctype": doctype})

	if share_name:
		frappe.delete_doc("DocShare", share_name)

@frappe.whitelist()
def set_permission(doctype, name, user, permission_to, value=1):
	"""Set share permission."""
	share_name = frappe.db.get_value("DocShare", {"user": user, "share_name": name,
		"share_doctype": doctype})
	value = int(value)
	if not share_name:
		if value:
			share = add(doctype, name, user, **{permission_to: 1})
		else:
			# no share found, nothing to remove
			share = {}
			pass
	else:
		share = frappe.get_doc("DocShare", share_name)
		share.flags.ignore_permissions = True
		share.set(permission_to, value)

		if not value:
			# un-set higher-order permissions too
			if permission_to=="read":
				share.read = share.write = share.share = 0
			elif permission_to=="write":
				share.write = share.share = 0

		share.save()

		if not (share.read or share.write or share.share):
			share.delete()
			share = {}

	return share

@frappe.whitelist()
def get_users(doctype, name, fields="*"):
	"""Get list of users with which this document is shared"""
	if isinstance(fields, (tuple, list)):
		fields = "`{0}`".format("`, `".join(fields))

	return frappe.db.sql("select {0} from tabDocShare where share_doctype=%s and share_name=%s".format(fields),
		(doctype, name), as_dict=True)

def get_shared(doctype, user=None, rights=None):
	"""Get list of shared document names for given user and DocType.

	:param doctype: DocType of which shared names are queried.
	:param user: User for which shared names are queried.
	:param rights: List of rights for which the document is shared. List of `read`, `write`, `share`"""

	if not user:
		user = frappe.session.user

	if not rights:
		rights = ["read"]

	condition = " and ".join(["`{0}`=1".format(right) for right in rights])

	return frappe.db.sql_list("select share_name from tabDocShare where user=%s and share_doctype=%s and {0}".format(condition),
		(user, doctype))

def get_shared_doctypes(user=None):
	"""Return list of doctypes in which documents are shared for the given user."""
	if not user:
		user = frappe.session.user

	return frappe.db.sql_list("select distinct share_doctype from tabDocShare where user=%s", user)
