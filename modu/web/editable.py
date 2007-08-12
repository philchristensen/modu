# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import implements, Interface, Attribute

from twisted import plugin

from modu.util import form
from modu.persist import storable

datatype_cache = {}

def __load_datatypes():
	import modu.datatypes
	for datatype_class in plugin.getPlugins(IDatatype, modu.datatypes):
		datatype = datatype_class()
		print " adding %s to cache" % datatype_class.__name__
		datatype_cache[datatype_class.__name__] = datatype


class IDatatype(Interface):
	def get_form_element(style, definition, storable):
		"""
		Take the given definition, and return a FormNode populated
		with data from the provided storable.
		"""


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
	def __init__(self, __config=None, **fields):
		for name, field in fields.iteritems():
			if not(isinstance(field, definition)):
				raise ValueError("'%s' is not a valid definition." % name)
			field.name = name
		
		self.update(fields)
	
	
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
		return datatype_cache[self['type']].get_form_element(self.name, 'list', self, storable)
	
	
	def get_detail_element(self, storable):
		"""
		Return a FormNode that represents this field in the resulting form.
		"""
		return datatype_cache[self['type']].get_form_element(self.name, 'detail', self, storable)


__load_datatypes()
