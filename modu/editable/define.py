# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains classes needed to define a basic itemdef.
"""

from zope.interface import classProvides, implements

from twisted import plugin

from modu import editable
from modu.util import form, tags
from modu.persist import storable, interp
from modu.web.user import AnonymousUser

def get_itemdefs(): 
	""" 
	Search the system path for any available IItemdef implementors. 
	""" 
	import modu.itemdefs
	itemdefs = {}
	for itemdef in plugin.getPlugins(editable.IItemdef, modu.itemdefs): 
		itemdefs[itemdef.name] = itemdef
	return itemdefs


class itemdef(dict):
	"""
	An itemdef essentially describes the data for a Storable.
	It can generate an editor form for its Storable, as well
	as providing behaviors and validation for that form.
	"""
	
	implements(editable.IItemdef, plugin.IPlugin)
	
	def __init__(self, __config=None, **fields):
		for name, field in fields.items():
			# I was pretty sure I knew how kwargs worked, but...
			if(name == '__config'):
				__config = field
				del fields[name]
			
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
				frm.children[name] = field.get_form_element(style, storable)
		
		if(not frm.has_submit_buttons()):
			frm['save'](type='submit', value='save', weight=1000)
			frm['cancel'](type='submit', value='cancel', weight=1000)
		
		def _validate(req, form):
			return self.validate(req, form, storable)
		
		def _submit(req, form):
			self.submit(req, form, storable)
		
		frm.validate = _validate
		frm.submit = _submit
		
		return frm
	
	
	def get_item_url(self, storable):
		# TODO: This should return something real, or call a function that can.
		return self.config.get('item_url', 'http://www.example.com')
	
	
	def validate(self, req, form, storable):
		if('cancel' in form.data[form.name]):
			return False
		
		# call validate hook on each field, return false if they do
		for field in form:
			if(field in self and 'validator' in self[field]):
				validator = self[field]['validator']
				if(validator):
					if not(validator(req, form, storable)):
						return False
			else:
				if not(form[field].validate(req, form)):
					return False
		
		# call prewrite_callback
		if('prewrite_callback' in self.config):
			result = self.config['prewrite_callback'](req, form, storable)
			if(result is False):
				return False
		
		return True
	
	def submit(self, req, form, storable):
		postwrite_fields = {}
		for name, definition in self.iteritems():
			if not(definition.get('implicit_save', True)):
				continue
			elif(definition.is_postwrite_field()):
				postwrite_fields[name] = definition
			else:
				# update storable data with form
				result = definition.update_storable(req, form, storable)
				if(result == False):
					#print '%s datatype returned false.' % name
					return
		
		# save storable data
		req.store.save(storable)
		
		# handle postwrite fields
		if(postwrite_fields):
			for name, definition in postwrite_fields.items():
				definition.update_storable(req, form, storable)
			req.store.save(storable)
		
		# call postwrite_callback
		if('postwrite_callback' in self.config):
			self.config['postwrite_callback'](req, form, storable)


class definition(dict):
	"""
	A definition represents a single field in an itemdef. It may or may not
	reflect a field of a Storable.
	"""
	
	inherited_attributes = ['weight', 'help', 'label']
	
	def __init__(self, **params):
		self.name = None
		self.itemdef = None
		self.update(params)
	
	
	def get_form_element(self, style, storable):
		frm = self.get_element(style, storable)
		
		classes = [self.__class__]
		while(classes):
			for cls in classes:
				if not(hasattr(cls, 'inherited_attributes')):
					continue
				for name in cls.inherited_attributes:
					if(name in self and name not in frm.attributes):
						frm.attributes[name] = self[name]
			classes = cls.__bases__
		
		for name, value in self.get('attributes', {}).iteritems():
			frm.attributes[name] = value
		
		if(self.get('link', False)):
			href = self.itemdef.get_item_url(storable)
			frm(prefix=tags.a(href=href, __no_close=True), suffix='</a>')
		return frm
	
	
	def update_storable(self, req, form, storable):
		form_name = '%s-form' % storable.get_table()
		if(form_name in form.data):
			form_data = form.data[form_name]
			if(self.name in form_data):
				setattr(storable, self.name, form_data[self.name].value)
		return True
	
	
	def is_postwrite_field(self):
		return False

