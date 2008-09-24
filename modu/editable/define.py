# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains classes needed to define a basic itemdef.

Although itemdefs are most readily used as part of the resources
defined in L{modu.editable.resource}, they can also be used
individually to present forms to modify Storables with.

Example::
	frm = itemdef.get_form(req, selected_item)
	if('theme' in itemdef.config):
	    frm.theme = itemdef.config['theme']
	
	if(frm.execute(req)):
	    # we regenerate the form because some fields don't know their
	    # value until after the form is saved (e.g., postwrite fields)
	    new_frm = itemdef.get_form(req, selected_item)
	    new_frm.errors = frm.errors
	    frm = new_frm
	else:
	    # If we haven't submitted the form, errors should definitely be empty
	    for field, err in frm.errors.items():
	        req.messages.report('error', err)
"""

import copy

from zope.interface import implements

from twisted import plugin
from twisted.python import util

from modu import editable
from modu.util import form, tags, theme, OrderedDict
from modu.persist import storable
from modu.web.user import AnonymousUser
from modu.web import app

def get_itemdefs(itemdef_module=None): 
	""" 
	Search the system path for any available itemdefs. 
	
	@return: all available itemdefs
	@rtype: dict(str=itemdef)
	"""
	if(itemdef_module is None):
		import modu.itemdefs
		#reload(modu.itemdefs)
		itemdef_module = modu.itemdefs
	
	itemdefs = {}
	for itemdef in plugin.getPlugins(editable.IItemdef, itemdef_module):
		if(itemdef.name):
			itemdefs[itemdef.name] = itemdef
	return itemdefs


def itemdef_cmp(a, b):
	"""
	A comparator function for sorting itemdefs.
	
	@return: C{cmp(a.config.get('weight', 0), b.config.get('weight', 0))}
	@rtype: int
	"""
	return cmp(a.config.get('weight', 0), b.config.get('weight', 0))


def get_itemdef_layout(req, itemdefs=None):
	"""
	Returns an OrderedDict instance containing the itemdef tree.
	
	Normally this is rendered as a navigation menu, and also provides
	templates with access to the other non-current itemdefs.
	
	The result has also been filtered to contain only the itemdefs and
	definitions that the req.user has access to. The data iteself is a
	clone, so modifications will have no effect.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param itemdefs: the itemdefs to layout, or None to layout all available itemdefs
	@type itemdefs: dict(str=itemdef)
	
	@return: the itemdef layout
	@rtype: L{modu.util.OrderedDict}(str=list)
	"""
	layout = util.OrderedDict()
	if(itemdefs is None):
		itemdefs = get_itemdefs()
	for name, itemdef in itemdefs.items():
		itemdef = clone_itemdef(itemdef)
		
		acl = itemdef.config.get('acl', '')
		if('acl' not in itemdef.config or req.user.is_allowed(acl)):
			cat = itemdef.config.get('category', 'other')
			layout.setdefault(cat, []).append(itemdef)
			layout[cat].sort(itemdef_cmp)
	return layout


def clone_itemdef(itemdef):
	"""
	Duplicate the provided itemdef in a sane fashion.
	
	@param itemdef: the itemdef to clone
	@type itemdef: L{modu.editable.define.itemdef}
	
	@return: the itemdef clone
	@rtype: L{modu.editable.define.itemdef}
	"""
	# this may need to be done a bit more delicately
	clone = copy.copy(itemdef)
	clone.config = copy.copy(clone.config)
	for name, field in clone.items():
		field.itemdef = clone
	return clone

class itemdef(OrderedDict):
	"""
	An itemdef describes the data of a Storable.
	It can generate an editor form for its Storable, as well
	as providing behaviors and validation for that form.
	
	@ivar config: Configuration details for this itemdef
	@type config: dict(str=type)
	
	@ivar name: The unique name of this itemdef, usually the DB table name.
	@type: str
	"""
	
	implements(editable.IItemdef, plugin.IPlugin)
	
	def __init__(self, __config=None, **fields):
		"""
		Create a new itemdef by specifying a list of fields.
		
		Fields can either be specified as additional keyword arguments to the
		itemdef constructor, or can be added via hash syntax. Items added via
		the constructor will be ordered randomly unless the 'weight'
		attribute is specified.
		
		Example::
		
			itemdef = define.itemdef(
			    __config        = dict(
			                        name        = 'customer',
			                        label       = 'Customers'
			                    ),
			    name            = string.StringField(
			                        label       = 'Name',
			                        listing     = True
			                    )
			)
			
			itemdef.config['no_delete'] = True
			
			itemdef['address']  = string.StringField(
			                        label       = 'Address',
			                        listing     = True
			                    )
			itemdef['city']     = string.StringField(
			                        label       = 'City',
			                        listing     = True
			                    )
			itemdef['state']    = string.SelectField(
			                        label       = 'State'
			                        options     = {'AK':'Arkansas', 'AL':'Alabama', ... }
			                    )
			itemdef['zip']      = string.StringField(
			                        label       = 'Zip',
			                        size        = 10
			                    )
		
		@param __config: the itemdef configuration data
		@type __config: dict
		
		@param **fields: the fields to display in the generated forms
		@type **fields: dict(str=L{modu.editable.define.definition})
		"""
		super(itemdef, self).__init__(self)
		
		keys = fields.keys()
		keys.sort(lambda a,b: cmp(fields[a].get('weight', 0), fields[b].get('weight', 0)))
		
		for name in keys:
			field = fields[name]
			# I was pretty sure I knew how kwargs worked, but...
			if(name == '__config'):
				__config = field
				continue
			
			# weight is meaningless once added
			field.pop('weight', None)
			self[name] = field
		
		if(__config):
			self.config = __config
			self.name = self.config.get('name', None)
		else:
			self.config = definition()
			self.name = None
	
	def __setitem__(self, name, field):
		if not(isinstance(field, definition)):
			raise ValueError("'%s' is not a valid definition." % name)
		
		super(itemdef, self).__setitem__(name, field)
		
		field.name = name
		field.itemdef = self
	
	def __getstate__(self):
		"""
		Integrate with OrderedDict serialization.
		"""
		data = super(itemdef, self).__getstate__()
		data['config'] = self.config
		data['name'] = self.name
		return data
	
	
	def __setstate__(self, data):
		"""
		Integrate with OrderedDict unserialization.
		"""
		super(itemdef, self).__setstate__(data)
		self.config = data['config']
		self.name = data['name']
	
	
	def get_name(self):
		"""
		This is a convenience function to be used when semi-retarded template
		engines (**ahem**cheetah**cough**) insist on returning a definition
		for a field called 'name' instead of the instance variable.
		
		@return: this itemdef's name
		@rtype: str
		"""
		return self.name
	
	
	def get_table(self):
		"""
		Return the database table used by this itemdef.
		
		This can be defined in the config array, but defaults to
		the name of the itemdef.
		
		@return: this itemdef's table
		@rtype: str
		"""
		return self.config.get('table', self.name)
	
	
	def allows(self, user, access='view'):
		"""
		A convenience function to check if a user is allowed to access this itemdef.
		
		TODO: Implement view/edit acl support.
		
		@param user: user attempting access
		@type user: L{modu.web.user.User}
		
		@param access: access requested
		@type access: str
		
		@return: True if user is allowed
		@rtype: bool
		"""
		if(user is None):
			# Should the default be off or on?
			return True
		return user.is_allowed(self.config.get('acl', []))
	
	
	def get_form(self, req, storable):
		"""
		Return a FormNode that represents this item in a detail view.
		
		If a user object is passed along, the resulting form will only
		contain fields the provided user is allowed to see.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param storable: The Storable instance to display.
		@type storable: L{modu.persist.storable.Storable}
		
		@return: Parent form object
		@rtype: L{modu.util.form.FormNode}
		"""
		frm = form.FormNode('%s-form' % storable.get_table())
		if(self.allows(req.user)):
			for name, field in self.items():
				if(name.startswith('_')):
					continue
				if(not field.get('detail', True)):
					continue
				if not(field.allows(req.user)):
					continue
				
				frm[name] = field.get_form_element(req, 'detail', storable)
		
		# if you don't want these, you may need to try something else
		#if(not frm.has_submit_buttons()):
		
		frm['save'](type='submit', value='save')
		frm['cancel'](type='submit', value='cancel')
		if not(self.config.get('no_delete', False)):
			frm['delete'](type='submit', value='delete',
						attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		def _validate(req, form):
			return self.validate(req, form, storable)
		
		def _submit(req, form):
			return self.submit(req, form, storable)
		
		frm.validate = _validate
		frm.submit = _submit
		
		return frm
	
	
	def get_search_form(self, req, storable):
		"""
		Return a FormNode that represents this item in a search view.
		
		If a user object is passed along, the resulting form will only
		contain search fields the provided user is allowed to see.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param storable: The Storable instance to display.
		@type storable: L{modu.persist.storable.Storable}
		
		@return: Parent form object
		@rtype: L{modu.util.form.FormNode}
		"""
		frm = form.FormNode('%s-search-form' % storable.get_table())
		if(self.allows(req.user)):
			for name, field in self.items():
				if(name.startswith('_')):
					continue
				if not(field.allows(req.user)):
					continue
				if not(field.get('search', False)):
					continue
				
				frm[name] = field.get_form_element(req, 'search', storable)
		
		if(len(frm) and not frm.has_submit_buttons()):
			frm['search'](type='submit', value='search', weight=1000)
			frm['clear_search'](type='submit', value='clear search', weight=1000)
		
		# search should always work...for now
		frm.validate = lambda r, f: True
		# submission doesn't really do much, since the editable
		# resource will handle that
		frm.submit = lambda r, f: True
		
		return frm
	
	
	def get_listing(self, req, storables):
		"""
		Return a FormNode that represents this item in a list view.
		
		This function returns a list of form objects that can be
		assembled into a list view (one "form" per row).
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param storable: The Storable instances to display.
		@type storable: list(L{modu.persist.storable.Storable})
		
		@return: List of parent form objects
		@rtype: L{modu.util.form.FormNode}
		"""
		forms = []
		if not(self.allows(req.user)):
			return forms
		
		for index in range(len(storables)):
			storable = storables[index]
			frm = form.FormNode('%s-row' % storable.get_table())
			for name, field in self.items():
				if(name.startswith('_')):
					continue
				if(not field.get('listing', False)):
					continue
				if not(field.allows(req.user)):
					continue
				
				frm[name] = field.get_form_element(req, 'listing', storable)
			
			def _validate(req, form):
				return self.validate(req, form, storable)
			
			def _submit(req, form):
				self.submit(req, form, storable)
			
			frm.validate = _validate
			frm.submit = _submit
			
			forms.append(frm)
		
		return forms
	
	
	def validate(self, req, frm, storable):
		"""
		The validation function for forms generated from this itemdef.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param frm: The current form
		@type frm: L{modu.util.form.FormNode}
		
		@param storable: The Storable instance associated with this form.
		@type storable: list(L{modu.persist.storable.Storable})
		
		@return: True if valid
		@rtype: bool
		"""
		form_data = req.data[frm.name]
		if(frm.submit_button.value == form_data.get('cancel', form.nil()).value):
			app.redirect(req.get_path(req.prepath, 'listing', storable.get_table()))
		elif(frm.submit_button.value == form_data.get('delete', form.nil()).value):
			if(self.delete(req, frm, storable)):
				app.redirect(req.get_path(req.prepath, 'listing', storable.get_table()))
			else:
				return False
		
		if(frm.submit_button.value != form_data.get('save', form.nil()).value):
			validator = frm.submit_button.attr('validator', None)
			if(callable(validator)):
				return validator(req, frm, storable)
			req.messages.report('error', "A custom submit button was used, but no validator function found.")
			return False
		else:
			# call validate hook on each field, return false if they do
			for field in frm:
				if(field in self and 'validator' in self[field]):
					validator = self[field]['validator']
					if(validator):
						if not(validator(req, frm, storable)):
							return False
				else:
					if not(frm[field].validate(req, frm)):
						return False
		
		return True
	
	
	def submit(self, req, form, storable):
		"""
		The submit function for forms generated from this itemdef.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param frm: The current form
		@type frm: L{modu.util.form.FormNode}
		
		@param storable: The Storable instance to submit.
		@type storable: list(L{modu.persist.storable.Storable})
		"""
		if(form.submit_button.value != 'save'):
			submitter = form.submit_button.attr('submitter', None)
			if(callable(submitter)):
				return submitter(req, form, storable)
			req.messages.report('error', "A custom submit button was used, but no submitter function found.")
			return False
		
		postwrite_fields = {}
		for name, definition in self.iteritems():
			if not(definition.get('implicit_save', True)):
				continue
			elif(definition.is_postwrite_field()):
				postwrite_fields[name] = definition
			else:
				# update storable data with form
				result = definition.update_storable(req, form, storable)
				if(result is False):
					#print '%s datatype returned false.' % name
					return False
		
		# call prewrite_callback
		if('prewrite_callback' in self.config):
			prewrite_callback = self.config['prewrite_callback']
			if not(isinstance(prewrite_callback, (list, tuple))):
				prewrite_callback = [prewrite_callback]
			for callback in prewrite_callback:
				if(callback(req, form, storable) is False):
					#print 'prewrite returned false'
					return False
		
		try:
			# save storable data
			req.store.save(storable, save_related_storables=False)
		except Exception, e:
			req.messages.report('error', "An exception occurred during primary save: %s" % e)
			return False
		
		postwrite_succeeded = True
		
		# handle postwrite fields
		if(postwrite_fields):
			for name, definition in postwrite_fields.items():
				if not(definition.update_storable(req, form, storable)):
					postwrite_succeeded = False
			try:
				req.store.save(storable)
			except Exception, e:
				req.messages.report('error', "An exception occurred during postwrite: %s" % e)
				postwrite_succeeded = False
		
		# call postwrite_callback
		if('postwrite_callback' in self.config):
			postwrite_callback = self.config['postwrite_callback']
			if not(isinstance(postwrite_callback, (list, tuple))):
				postwrite_callback = [postwrite_callback]
			for callback in postwrite_callback:
				if not(callback(req, form, storable)):
					postwrite_succeeded = False
		
		if(req.postpath and req.postpath[-1] == 'new'):
			app.redirect(req.get_path(req.prepath, 'detail', storable.get_table(), storable.get_id()))
		
		if(postwrite_succeeded):
			req.messages.report('message', 'Your changes have been saved.')
		else:
			req.messages.report('error', 'There was an error in the postwrite process, but primary record data was saved.')
		
		return postwrite_succeeded
	
	def delete(self, req, form, storable):
		"""
		The delete function for forms generated from this itemdef.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param frm: The current form
		@type frm: L{modu.util.form.FormNode}
		
		@param storable: The Storable instance to delete.
		@type storable: list(L{modu.persist.storable.Storable})
		
		@return: True if deleted
		@rtype: bool
		"""
		if(self.config.get('no_delete', False)):
			return False
		
		if('predelete_callback' in self.config):
			result = self.config['predelete_callback'](req, form, storable)
			if(result is False):
				return False
		
		deleted_id = storable.get_id()
		deleted_table = storable.get_table()
		storable.get_store().destroy(storable, self.config.get('delete_related_storables', False))
		
		if('postdelete_callback' in self.config):
			self.config['postdelete_callback'](req, form, storable)
		
		req.messages.report('message', "Record #%d in %s was deleted." % (deleted_id, deleted_table))
		
		return True


class definition(dict):
	"""
	A definition represents a single field in an itemdef.
	
	This is an abstract class.
	
	@cvar inherited_attributes: a list of attributes that will be
		automatically set on the resulting form node instance if
		they are not already defined on the FormNode returned by
		L{get_element()}
	@type inherited_attributes: list(str)
	
	@ivar name: name of this field definition. This variable is set
		by the itemdef when a definition is added to it.
	@type name: str
	
	@ivar itemdef: parent itemdef of this field definition. This variable is set
		by the itemdef when a definition is added to it.
	@type itemdef: L{modu.editable.define.itemdef}
	"""
	
	# inherited attributes will be automatically set on the resulting
	# form node instance only if they are not already defined.
	inherited_attributes = ['weight', 'help', 'label']
	
	def __init__(self, **params):
		"""
		Create a new field definition.
		
		Example::
			# the attributes of this example field are available on all fields
			name            = define.definition(            # Normally you wouldn't ever instantiate this
			    label       = 'Customer Name',              # [o] The label to appear on this form item
			    help        = "Enter the customer name",    # [o] Help text (tooltip) for this field.
			    listing     = True,                         # [o] Should this field appear in list view?
			    link        = True,                         # [o] If True, this field will have a hyperlink added as a
			                                                # form prefix/suffix that will link to the detail URL.
			    detail      = True,                         # [o] Should this field appear in detail view?
			    read_only   = False,                        # [o] If supported, this field should be uneditable/disabled
			    search      = False,                        # [o] Should this field appear in the listing search form?
			    weight      = 0,                            # [o] The weight (relative position) of this field
			    attributes  = {}                            # [o] Attributes set here will define or override 
			                                                # values on the resulting FormNode instance.
			)
		"""
		self.name = None
		self.itemdef = None
		self.update(params)
	
	
	def allows(self, user, access='view'):
		"""
		A convenience function to check if a user is allowed to access this field.
		
		TODO: Implement view/edit acl support.
		
		@param user: user attempting access
		@type user: L{modu.web.user.User}
		
		@param access: access requested
		@type access: str
		
		@return: True if user is allowed
		@rtype: bool
		"""
		if(user is None):
			return True
		return user.is_allowed(self.get('acl', []))
	
	
	def get_column_name(self):
		"""
		Return the proper SQL column name for this field.
		"""
		return self.get('column', self.name)
	
	
	def get_form_element(self, req, style, storable):
		"""
		Get a FormNode element that represents this field.
		
		The parent itemdef class will call this function, which will
		call the get_element() method, and set a few default values.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param style: Generate for 'listing', 'search', or 'detail' views.
		@type style: str
		
		@param storable: The Storable instance to fill form data with.
		@type storable: L{modu.persist.storable.Storable} subclass
		
		@return: form element
		@rtype: L{modu.util.form.FormNode}
		"""
		frm = self.get_element(req, style, storable)
		
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
		
		# Since the templates take care of the wrapper, all
		# elements are defined as basic elements unless set
		# explicitly by the field definition.
		if(style != 'search' and 'basic_element' not in frm.attributes):
			frm(basic_element=True)
		
		if(style == 'listing' and self.get('link', False)):
			href = req.get_path(req.prepath, 'detail', storable.get_table(), storable.get_id())
			frm(prefix=tags.a(href=href, __no_close=True), suffix='</a>')
		
		if(self.get('required', False)):
			frm(required=True)
		
		if(callable(self.get('form_alter', None))):
			self['form_alter'](req, style, frm, storable, self)
		
		return frm
	
	
	def get_element(self, req, style, storable):
		"""
		Render a FormNode element for this field definition.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param style: Generate for 'listing', 'search', or 'detail' views.
		@type style: str
		
		@param storable: The Storable instance to fill form data with.
		@type storable: L{modu.persist.storable.Storable} subclass
		
		@return: form element
		@rtype: L{modu.util.form.FormNode}
		"""
		raise NotImplementedError('definition::get_element()');
	
	
	def update_storable(self, req, form, storable):
		"""
		Given the posted data in req, update provided storable with this field's content.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param frm: The current form
		@type frm: L{modu.util.form.FormNode}
		
		@param storable: The Storable instance to fill form data with.
		@type storable: L{modu.persist.storable.Storable} subclass
		
		@return: False to abort the save, True to continue
		@rtype: bool
		"""
		form_name = '%s-form' % storable.get_table()
		if(form_name in req.data):
			form_data = req.data[form_name]
			if(self.name in form_data):
				setattr(storable, self.get_column_name(), form_data[self.name].value)
		return True
	
	
	def get_search_value(self, value, req, frm):
		"""
		Convert the value in this field to a search value.
		
		The value returned by this function will be included in the
		constraint array that is rendered to SQL. The most common
		reason to override this field is to return a RAW SQL value,
		or other non-string constraint.
		
		@return: a value suitable for inclusion in L{modu.persist.sql.build_where()}
			constraint argument dictionary
		"""
		if(value is None):
			return value
		return value.value
	
	
	def is_postwrite_field(self):
		"""
		Should this field be written normally, or after the main write to the database?
		
		@return: True if written after the main DB write.
		@rtype: bool
		"""
		return False

