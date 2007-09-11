# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains classes needed to define a basic itemdef.
"""

import copy

from zope.interface import implements

from twisted import plugin
from twisted.python import util

from modu import editable
from modu.util import form, tags, theme
from modu.persist import storable, interp
from modu.web.user import AnonymousUser
from modu.web import app

def get_itemdefs(): 
	""" 
	Search the system path for any available itemdefs. 
	""" 
	import modu.itemdefs
	itemdefs = {}
	for itemdef in plugin.getPlugins(editable.IItemdef, modu.itemdefs):
		if(itemdef.name):
			itemdefs[itemdef.name] = itemdef
	return itemdefs


def itemdef_cmp(a, b):
	return cmp(a.config.get('weight', 0), b.config.get('weight', 0))


def get_itemdef_layout(req, itemdefs=None):
	user = req.user
	layout = util.OrderedDict()
	if(itemdefs is None):
		itemdefs = get_itemdefs()
	for name, itemdef in itemdefs.items():
		itemdef = clone_itemdef(itemdef)
		itemdef.config['base_path'] = req.get_path(*req.app.tree.prepath)
		acl = itemdef.config.get('acl', 'view item')
		if('acl' not in itemdef.config or user.is_allowed(acl)):
			cat = itemdef.config.get('category', 'other')
			layout.setdefault(cat, []).append(itemdef)
			layout[cat].sort(itemdef_cmp)
	return layout


def clone_itemdef(itemdef):
	"""
	Duplicate the provided itemdef in a sane fashion.
	"""
	# this may need to be done a bit more delicately
	clone = copy.copy(itemdef)
	clone.config = copy.copy(clone.config)
	for name, field in clone.items():
		field.itemdef = clone
	return clone

class itemdef(dict):
	"""
	An itemdef describes the data of a Storable.
	It can generate an editor form for its Storable, as well
	as providing behaviors and validation for that form.
	"""
	
	implements(editable.IItemdef, plugin.IPlugin)
	
	def __init__(self, __config=None, **fields):
		"""
		Create a new itemdef by specificying a list of fields.
		"""
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
			self.name = self.config.get('name', None)
		else:
			self.config = definition()
			self.name = None
		
		self.update(fields)
	
	def get_name(self):
		"""
		This is a convenience function to be used when semi-retarded template
		engines (**ahem**cheetah**cough**) insist on returning a definition
		for a field called 'name' instead of the instance variable.
		"""
		return self.name
	
	def get_table(self):
		"""
		Return the database table used by this itemdef.
		
		This can be defined in the config array, but defaults to
		the name of the itemdef.
		"""
		return self.config.get('table', self.name)
	
	def get_form(self, storable, user=None):
		"""
		Return a FormNode that represents this item in a detail view.
		
		If a user object is passed along, the resulting form will only
		contain fields the provided user is allowed to see.
		"""
		frm = form.FormNode('%s-form' % storable.get_table())
		if(user is None or user.is_allowed(self.get('acl', self.config.get('acl', [])))):
			for name, field in self.items():
				if(name.startswith('_')):
					continue
				if(not field.get('detail', True)):
					continue
				if not(user is None or user.is_allowed(field.get('acl', self.config.get('acl', [])))):
					continue
				
				frm.children[name] = field.get_form_element('detail', storable)
				frm.children[name].parent = frm
		
		if(not frm.has_submit_buttons()):
			frm['save'](type='submit', value='save', weight=1000)
			frm['cancel'](type='submit', value='cancel', weight=1000)
			frm['cancel'](type='submit', value='cancel', weight=1000)
		
		def _validate(req, form):
			return self.validate(req, form, storable)
		
		def _submit(req, form):
			self.submit(req, form, storable)
		
		frm.validate = _validate
		frm.submit = _submit
		
		return frm
	
	
	def get_search_form(self, storable, user=None):
		"""
		Return a FormNode that represents this item in a detail view.
		
		If a user object is passed along, the resulting form will only
		contain fields the provided user is allowed to see.
		"""
		frm = form.FormNode('%s-search-form' % storable.get_table())
		if(user is None or user.is_allowed(self.get('acl', self.config.get('acl', [])))):
			for name, field in self.items():
				if(name.startswith('_')):
					continue
				if(not field.get('detail', True)):
					continue
				if not(user is None or user.is_allowed(field.get('acl', self.config.get('acl', [])))):
					continue
				if not(field.get('search', False)):
					continue
				
				frm.children[name] = field.get_form_element('detail', storable)
				frm.children[name].parent = frm
		
		if(not frm.has_submit_buttons()):
			frm['search'](type='submit', value='search', weight=1000)
			frm['clear_search'](type='submit', value='clear search', weight=1000)
		
		# search should always work...for now
		frm.validate = lambda r, f: True
		# submission doesn't really do much, since the editable
		# resource will handle that
		frm.submit = lambda r, f: True
		
		return frm
	
	
	def get_listing(self, storables, user=None):
		"""
		Return a FormNode that represents this item in a list view.
		
		This function returns a list of form objects that can be
		assembled into a list view (one "form" per row).
		"""
		forms = []
		for index in range(len(storables)):
			storable = storables[index]
			frm = form.FormNode('%s-row' % storable.get_table())
			if(user is None or user.is_allowed(self.get('acl', self.config.get('acl', [])))):
				for name, field in self.items():
					if(name.startswith('_')):
						continue
					if(not field.get('listing', False)):
						continue
					if not(user is None or user.is_allowed(field.get('acl', self.config.get('acl', [])))):
						continue
				
					frm.children[name] = field.get_form_element('listing', storable)
			
			def _validate(req, form):
				return self.validate(req, form, storable)
			
			def _submit(req, form):
				self.submit(req, form, storable)
			
			frm.validate = _validate
			frm.submit = _submit
			
			forms.append(frm)
		
		return forms
	
	
	def get_item_url(self, storable):
		"""
		Given the provided storable, return a path that would take you to the item's detail page.
		"""
		#TODO: Make this customizable.
		return '%s/detail/%s/%d' % (self.config['base_path'], storable.get_table(), storable.get_id())
	
	
	def validate(self, req, form, storable):
		if('cancel' in form.data[form.name]):
			app.redirect('%s/listing/%s' % (self.config['base_path'], storable.get_table()))
		
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
		# this seems like a strange place for this, since prewrites aren't
		# explicitly validation, but i think it's okay for now.
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
		
		if(req.get('modu.messages')):
			req.messages.report('message', 'Your changes have been saved.')
		
		# handle postwrite fields
		if(postwrite_fields):
			for name, definition in postwrite_fields.items():
				definition.update_storable(req, form, storable)
			req.store.save(storable)
		
		# call postwrite_callback
		if('postwrite_callback' in self.config):
			self.config['postwrite_callback'](req, form, storable)
		
		if(req.app.tree.postpath and req.app.tree.postpath[-1] == 'new'):
			app.redirect(self.get_item_url(storable))


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
		
		if(style == 'listing' and self.get('link', False)):
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
	
	
	def get_search_value(self, value):
		return value

	
	def is_postwrite_field(self):
		return False

