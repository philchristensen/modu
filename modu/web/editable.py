# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import implements, Interface, Attribute

from twisted import plugin

from modu.util import form, tags
from modu.persist import storable
from modu.web.user import AnonymousUser

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
	__itemdef__ = Attribute("""
		Contains an object/datastructure representing the
		fields and behaviors for this object's editable
		forms.
	""")


class Field(object):
	def get_form_element(self, name, style, definition, storable):
		frm = self.get_element(name, style, definition, storable)
		if(definition.get('link', False)):
			href = definition.itemdef.get_item_url(storable)
			frm(prefix=tags.a(href=href, __no_close=True), suffix='</a>')
		return frm


class itemdef(dict):
	def __init__(self, __config=None, **fields):
		for name, field in fields.items():
			if not(isinstance(field, definition)):
				raise ValueError("'%s' is not a valid definition." % name)
			field.name = name
			field.itemdef = self
		
		if(__config):
			self.config = __config
		else:
			self.config = definition()
		
		self.update(fields)
	
	
	def get_form(self, style, storable, user=None):
		"""
		Return a FormNode that represents this item
		"""
		if(user is None):
			user = AnonymousUser()
		frm = form.FormNode('%s-form' % storable.get_table())
		if(user.is_allowed(self.get('acl', self.config.get('default_acl', [])))):
			for name, field in self.items():
				if(name.startswith('_')):
					continue
				if(style == 'list' and not field.get('list', False)):
					continue
				if(style == 'detail' and not field.get('detail', True)):
					continue
				if not(user.is_allowed(field.get('acl', self.config.get('default_acl', [])))):
					continue
				frm.children[name] = field.get_element(style, storable)
		
		def _validate(req, form):
			self.validate(req, form, storable)
		
		def _submit(req, form):
			self.submit(req, form, storable)
		
		frm.validate = _validate
		frm.submit = _submit
		
		return frm
	
	
	def get_item_url(self, storable):
		# TODO: This should return something real, or call a function that can.
		return self.config.get('item_url', 'http://www.example.com')
	
	
	def validate(self, req, form, storable):
		# TODO: call prewrite_callback
		# TODO: call validate hook on each field, return false if they do
		pass
	
	def submit(self, req, form, storable):
		postwrite_fields = []
		for name, definition in self.iteritems():
			datatype = datatype_cache[definition['type']]
			if(definition.get('implicit_save', True)):
				continue
			elif(datatype.is_postwrite_field()):
				postwrite_fields.append(name)
			else:
				# TODO: pass each datatype form data, ask for result
				# TODO: if None, skip this field
				# TODO: update storable data with form
				pass
		# TODO: handle postwrite fields
		# TODO: call postwrite_callback
		pass


class definition(dict):
	def __init__(self, **params):
		self.name = None
		self.itemdef = None
		self.update(params)
	
	
	def get_element(self, style, storable):
		"""
		Return a FormNode that represents this field in the resulting form.
		"""
		return datatype_cache[self['type']].get_form_element(self.name, style, self, storable)


__load_datatypes()
