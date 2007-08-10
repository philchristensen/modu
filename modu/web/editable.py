# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id: twist.py 414 2007-08-09 19:52:15Z phil $
#
# See LICENSE for details

from zope.interface import implements, Interface, Attribute

from modu.util import form
from modu.persist import storable

class IEditable(storable.IStorable):
	def get_itemdef(self):
		"""
		Return an object/datastructure representing the
		fields and behaviors for this object's editable
		forms.
		
		Maybe this should be a class variable instead?
		If it were, we could use something cool like
		descriptors to implement magic.
		"""

class itemdef(dict):
	def __init__(self, __config=definition(), **fields):
		for name, field in fields.iteritems():
			if not(isinstance(field, definition)):
				raise ValueError("'%s' is not a valid definition." % name)
			field.name = name
		
		self.update(kwargs)
	
	def get_detail_form(self, storable):
		"""
		Return a FormNode that represents this item
		"""
		frm = form.FormNode('%s-form' % storable.get_table())
		for name, field in self.iteritems():
			frm.children[name] = field.get_detail_element(storable)
		# set special array stuff, like pre and postwrite (as callbacks)
		return frm
	
	def get_list_form(self, storable):
		"""
		Return a FormNode that represents this item
		"""
		frm = form.FormNode(form_name)
		for name, field in self.iteritems():
			frm.children[name] = field.get_list_element(storable)
		# set special array stuff, like pre and postwrite (as callbacks)
		# set frm.theme to a special list-drawing theme
		return frm

class definition(dict):
	def __init__(self, **params):
		self.name = None
		self.update(params)
	
	def get_list_element(self, storable):
		"""
		Return a FormNode that represents this field in the resulting form.
		"""
		attribs = {}
		# iterate through definition to define form element
		# load storable content
		frm = form.FormNode(self.name)(**attribs)
		return frm
	
	def get_detail_element(self, storable):
		"""
		Return a FormNode that represents this field in the resulting form.
		"""
		attribs = {}
		# iterate through definition to define form element
		# load storable content
		frm = form.FormNode(self.name)(**attribs)
		return frm

sample_itemdef = itemdef(
	__config		= definition(
						postwrite_callback			= 'user_postwrite',
						prewrite_callback			= 'user_prewrite'
					),
	
	id				= definition(
						postwrite_callback			= 'user_postwrite',
						prewrite_callback			= 'user_prewrite'
					)
)