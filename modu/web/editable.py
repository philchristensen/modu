# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Provides classes for implementing editors for Storable objects.
"""

from zope.interface import implements, Interface, Attribute

from twisted import plugin

from modu.util import form, tags
from modu.persist import storable, interp
from modu.web import resource, app
from modu.web.user import AnonymousUser

datatype_cache = {}

def __load_datatypes():
	"""
	Search the system path for any available IDatatype implementors.
	"""
	import modu.datatypes
	for datatype_class in plugin.getPlugins(IDatatype, modu.datatypes):
		datatype = datatype_class()
		print " adding %s to cache" % datatype_class.__name__
		datatype_cache[datatype_class.__name__] = datatype


class IDatatype(Interface):
	"""
	I can take a field definition from an Editable itemdef and return a form object.
	Datatypes can also answer various questions about how that form should be handled.
	"""
	
	def get_form_element(self, style, definition, storable):
		"""
		Take the given definition, and return a FormNode populated
		with data from the provided storable.
		"""
	
	def update_storable(self, req, definition, storable):
		"""
		The fields of this storable will already be populated in
		most scenarios, but this function can be implemented by
		datatypes who wish to calculate a value based on
		more complex POST data.
		"""
	
	def is_postwrite_field(self):
		"""
		Some fields (particularly file uploads) may need to write their
		data after all other "standard" data has been written. For example,
		they may require the Storable id. If this function returns True,
		the items will be ignored during the regular process and given a
		chance to write after the main record has been saved.
		"""


class IEditable(storable.IStorable):
	"""
	An IEditable is an IStorable that knows about itemdefs.
	"""
	def get_itemdef(self):
		"""
		Contains an object/datastructure representing the
		fields and behaviors for this object's editable
		forms.
		"""


class EditorResource(resource.CheetahTemplateResource):
	"""
	A basic editor resource. Displays editors for any registered
	IEditable-instantiating Factory.
	"""
	def get_paths(self):
		return ['/edit', '/autocomplete']
	
	def prepare_content(self, req):
		if not(len(req.app.tree.postpath) >= 2):
			app.raise404('/'.join(req.app.tree.postpath))
		if not(req.store.has_factory(req.app.tree.postpath[0])):
			app.raise404('/'.join(req.app.tree.postpath))
		
		if(req.app.tree.prepath[0] == 'autocomplete'):
			self.prepare_autocomplete(req)
		else:
			self.prepare_editor(req)
	
	def prepare_autocomplete(self, req):
		item = req.store.load_one(req.app.tree.postpath[0], {}, __limit=1)
		if not(IEditable.providedBy(item)):
			app.raise500('%r is does not implement the IEditable interface.')
		
		itemdef = item.get_itemdef()
		definition = itemdef[req.app.tree.postpath[1]]
		
		value = definition['fvalue']
		label = definition['flabel']
		table = definition['ftable']
		
		ac_query = "SELECT %s, %s FROM %s WHERE %s LIKE %%s" % (value, label, table, label)
		
		post_data = form.NestedFieldStorage(req)
		results = req.store.pool.runQuery(ac_query, ['%%%s%%' % post_data['q'].value])
		
		content = ''
		for result in results:
			content += "%s|%d\n" % (result[label], result[value])
		
		app.raise200([('Content-Type', 'text/plain')], [content])
	
	def prepare_editor(self, req):
		item = req.store.load_one(req.app.tree.postpath[0], {'id':int(req.app.tree.postpath[1])})
		if not(IEditable.providedBy(item)):
			app.raise500('%r is does not implement the IEditable interface.')
		
		form = item.get_itemdef().get_form('detail', item)
		if(form.execute(req)):
			form = item.get_itemdef().get_form('detail', item)
		
		self.set_slot('form', form.render(req))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'editable-detail.html.tmpl' 


class Field(object):
	"""
	A convenient superclass for all IDatatype implementors.
	"""
	
	inherited_attributes = ['weight', 'help', 'label']
	
	def get_form_element(self, name, style, definition, storable):
		frm = self.get_element(name, style, definition, storable)
		
		classes = [self.__class__]
		while(classes):
			for cls in classes:
				if not(hasattr(cls, 'inherited_attributes')):
					continue
				for name in cls.inherited_attributes:
					if(name in definition and name not in frm.attributes):
						frm.attributes[name] = definition[name]
			classes = cls.__bases__
		
		for name, value in definition.get('attributes', {}).iteritems():
			frm.attributes[name] = value
		
		if(definition.get('link', False)):
			href = definition.itemdef.get_item_url(storable)
			frm(prefix=tags.a(href=href, __no_close=True), suffix='</a>')
		return frm
	
	def update_storable(self, name, req, form, definition, storable):
		form_name = '%s-form' % storable.get_table()
		if(form_name in form.data):
			form_data = form.data[form_name]
			if(name in form_data):
				setattr(storable, name, form_data[name].value)
		return True
	
	def is_postwrite_field(self):
		return False


class itemdef(dict):
	"""
	An itemdef essentially describes the data for a Storable.
	It can generate an editor form for its Storable, as well
	as providing behaviors and validation for that form.
	"""
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
				frm.children[name] = field.get_element(style, storable)
		
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
			datatype = datatype_cache[definition['type']]
			if not(definition.get('implicit_save', True)):
				continue
			elif(datatype.is_postwrite_field()):
				postwrite_fields[name] = datatype
			else:
				# update storable data with form
				result = datatype.update_storable(name, req, form, definition, storable)
				if(result == False):
					#print '%s datatype returned false.' % name
					return
		
		# save storable data
		req.store.save(storable)
		
		# handle postwrite fields
		if(postwrite_fields):
			for name, datatype in postwrite_fields.items():
				datatype.update_storable(name, req, form, self[name], storable)
			req.store.save(storable)
		
		# call postwrite_callback
		if('postwrite_callback' in self.config):
			self.config['postwrite_callback'](req, form, storable)


class definition(dict):
	"""
	A definition represents a single field in an itemdef. It may or may not
	reflect a field of a Storable.
	"""
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
