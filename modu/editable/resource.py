# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains resources for configuring a default admin interface.
"""

import os.path, copy

from modu.web import resource, app, user
from modu.editable import define
from modu.util import form, theme, tags
from modu.persist import page, storable, sql

def select_template_root(req, template):
	import modu
	
	template_root = os.path.join(req.approot, 'template')
	if(os.access(os.path.join(template_root, template), os.F_OK)):
		return template_root
	
	return os.path.join(os.path.dirname(modu.__file__), 'assets', 'default-template')


def validate_login(req, form):
	"""
	Validation callback for login form.
	
	Ensures values in username and password fields.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param form: the form being validated
	@type form: L{modu.util.form.FormNode}
	
	@return: True if all data is entered
	@rtype: bool
	"""
	if not(form.data[form.name]['username']):
		form.set_form_error('username', "Please enter your username.")
	if not(form.data[form.name]['password']):
		form.set_form_error('password', "Please enter your password.")
	return not form.has_errors()
	


def submit_login(req, form):
	"""
	Submission callback for login form.
	
	Logs in the user using crypt()-based passwords.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param form: the form being validated
	@type form: L{modu.util.form.FormNode}
	"""
	req.store.ensure_factory('user', user.User)
	form_data = form.data[form.name]
	encrypt_sql = sql.interp('%%s = ENCRYPT(%s, SUBSTRING(crypt, 1, 2))', [form_data['password'].value])
	u = req.store.load_one('user', username=form_data['username'].value, crypt=sql.RAW(encrypt_sql))
	if(u):
		req.session.set_user(u)
	else:
		req.messages.report('error', "Sorry, that login was incorrect.")


def configure_store(req, itemdef):
	"""
	Set up the current request environment for this itemdef.
	
	For now, this simply registers the appropriate factories for the
	given itemdef instance.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param itemdef: the itemdef to load factories for
	@type itemdef: L{modu.editable.define.itemdef}
	"""
	table_name = itemdef.config.get('table', itemdef.name)
	if('factory' in itemdef.config):
		req.store.register_factory(table_name, itemdef.config['factory'])
	elif('model_class' in itemdef.config):
		req.store.ensure_factory(table_name, itemdef.config['model_class'])
	else:
		req.store.ensure_factory(table_name)


class AdminResource(resource.CheetahTemplateResource):
	"""
	Provides a configurable administrative/content management interface.
	
	Adding an instance of this resource to a modu site allows you to use
	itemdefs to define the content management interfaces for your database
	content.
	
	@ivar path: The path this instance is installed at.
	@type path: str
	
	@ivar template: The template the current request has selected.
	@type template: str
	"""
	def __init__(self, path=None, **options):
		"""
		Create an instance of the admin tool.
		
		@param path: The path this instance should respond to.
		@type path: str
		"""
		if(path is None):
			path = '/admin'
		self.path = path
		self.options = options
	
	
	def get_paths(self):
		"""
		This resource will respond to /admin by default.
		
		"%s/logout" % self.path will also be registered.
		
		@see: L{modu.web.resource.IResource.get_paths()}
		"""
		return [self.path, '%s/logout' % self.path]
	
	
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		user = req['modu.user']
		self.set_slot('user', user)
		if(user and user.get_id()):
			if(req.prepath[-1] == 'logout'):
				req.session.set_user(None)
				app.redirect(req.get_path(self.path))
			
			itemdefs = define.get_itemdefs()
			
			# get_itemdef_layout adds some data and clones the itemdef
			self.itemdef_layout = define.get_itemdef_layout(req, itemdefs)
			
			# FIXME: This is inelegant -- we need to get at the cloned itemdef
			# as it already has some config data in it (because of get_itemdef_layout)
			
			# Is this an issue anymore? since the useful itemdef functions now get a
			# reference to the request, we don't put any dynamic config data in the
			# itemdef anymore.
			
			# Maybe we still need it for user permission support?
			itemdefs = dict([(itemdef.name, itemdef) for itemdef in
								reduce(lambda x, y: x+y, self.itemdef_layout.values())])
			
			self.set_slot('itemdef_layout', self.itemdef_layout)
			
			if(len(req.postpath) > 1):
				itemdef_name = req.postpath[1]
				# we just need to select the right itemdef
				selected_itemdef = itemdefs.get(itemdef_name)
				
				self.set_slot('selected_itemdef', selected_itemdef)
				
				if(selected_itemdef):
					configure_store(req, selected_itemdef)
					
					if(req.postpath[0] == 'detail'):
						self.prepare_detail(req, selected_itemdef)
					elif(req.postpath[0] == 'autocomplete'):
						self.prepare_autocomplete(req, selected_itemdef)
					else:
						self.prepare_listing(req, selected_itemdef)
				else:
					app.raise403()
			else:
				default_listing = self.options.get('default_listing')
				if(default_listing):
					redirect_path = req.get_path(self.path, 'listing', default_listing)
					app.redirect(redirect_path)
				
				app.raise404('There is no item list at the path: %s' % req['REQUEST_URI'])
		else:
			self.set_slot('itemdef_layout', None)
			self.set_slot('selected_itemdef', None)
			self.prepare_login(req)
	
	
	def prepare_login(self, req):
		"""
		Handle creation and display of a login page.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
		self.template = 'admin-login.html.tmpl'
		
		login_form = form.FormNode('login')
		login_form['username'](type='textfield', label='Username')
		login_form['password'](type='password', label='Password')
		login_form['submit'](type='submit', value='login')
		login_form.validate = validate_login
		login_form.submit = submit_login
		
		if(login_form.execute(req) and req.session.get_user()):
			app.redirect(req.get_path(self.path))
		else:
			self.set_slot('login_form', login_form.render(req))
	
	
	def prepare_listing(self, req, itemdef):
		"""
		Handle creation and display of the listing page.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to use to generate the listing
		@type itemdef: L{modu.editable.define.itemdef}
		"""
		self.template = itemdef.config.get('list_template', 'admin-listing.html.tmpl')
		table_name = itemdef.config.get('table', itemdef.name)
		
		query_data = form.NestedFieldStorage(req)
		pager = page.Paginator()
		if('page' in query_data):
			pager.page = int(query_data['page'].value)
		else:
			pager.page = 1
		pager.per_page = itemdef.config.get('per_page', 25)
		
		# create a fake storable to make itemdef/form happy
		search_storable = storable.Storable(table_name)
		# give it a factory so fields can use its store reference
		search_storable.set_factory(req.store.get_factory(table_name))
		# build the form tree
		search_form = itemdef.get_search_form(req, search_storable)
		# get any saved search data
		session_search_data = req.session.setdefault('search_form', {}).setdefault(itemdef.name, {})
		
		if(search_form.execute(req)):
			search_data = search_form.data[search_form.name]
			if('clear_search' in search_data):
				req.session.setdefault('search_form', {})[itemdef.name] = {}
				app.redirect(req.get_path(self.path, 'listing', table_name))
			
			for submit in search_form.find_submit_buttons():
				search_data.pop(submit.name, None)
			
			data = {}
			for key, value in search_data.items():
				session_search_data[key] = value.value
				result = itemdef[key].get_search_value(value.value)
				if(result is not None):
					if(isinstance(result, dict)):
						for key, value in result.items():
							data[key] = value
					else:
						data[key] = result
			
			items = pager.get_results(req.store, table_name, data)
		elif(session_search_data):
			search_data = {search_form.name:session_search_data}
			search_form.load_data(search_data)
			
			data = {}
			for key, value in session_search_data.items():
				result = itemdef[key].get_search_value(value)
				if(result is not None):
					if(isinstance(result, dict)):
						for key, value in result.items():
							data[key] = value
					else:
						data[key] = result
			
			items = pager.get_results(req.store, table_name, data)
		else:
			items = pager.get_results(req.store, table_name, {})
		
		forms = itemdef.get_listing(req, items)
		thm = theme.Theme(req)
		
		template_variable_callback = itemdef.config.get('template_variable_callback')
		if(callable(template_variable_callback)):
			for key, value in template_variable_callback(req, forms, search_storable).items():
				self.set_slot(key, value)
		
		self.set_slot('items', items)
		self.set_slot('pager', pager)
		self.set_slot('search_form', search_form.render(req))
		self.set_slot('page_guide', thm.page_guide(pager, req.get_path(req.path)))
		self.set_slot('forms', forms)
		self.set_slot('theme', thm)
	
	
	def prepare_detail(self, req, itemdef):
		"""
		Handle creation and display of the detail page.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to use to generate the form
		@type itemdef: L{modu.editable.define.itemdef}
		"""
		self.template = itemdef.config.get('detail_template', 'admin-detail.html.tmpl')
		self.set_slot('form', None)
		if(len(req.postpath) > 2):
			item_id = req.postpath[2]
			table_name = itemdef.config.get('table', itemdef.name)
			
			if(item_id == 'new'):
				selected_item = storable.Storable(table_name)
				# we can be sure the factory is there, because configure_store
				# already took care of it during prepare_content
				factory = req.store.get_factory(table_name)
				selected_item.set_factory(factory)
			else:
				try:
					selected_item = req.store.load_one(table_name, {'id':int(item_id)})
				except TypeError:
					app.raise404('There is no detail view at the path: %s' % req['REQUEST_URI'])
			
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
			
			template_variable_callback = itemdef.config.get('template_variable_callback')
			if(callable(template_variable_callback)):
				result = template_variable_callback(req, frm, selected_item)
				if(isinstance(result, dict)):
					for key, value in result.items():
						self.set_slot(key, value)
			
			self.set_slot('form', frm)
			self.set_slot('theme', frm.theme(req))
			self.set_slot('selected_item', selected_item)
		else:
			app.raise404('There is no detail view at the path: %s' % req['REQUEST_URI'])
	
	
	def prepare_autocomplete(self, req, itemdef):
		"""
		Provide AJAX support for autocomplete fields.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to provide autocompletion for
		@type itemdef: L{modu.editable.define.itemdef}
		"""
		definition = itemdef[req.postpath[2]]
		post_data = form.NestedFieldStorage(req)
		results = []
		
		if('q' in post_data):
			partial = post_data['q'].value
		else:
			partial = None
		
		content = ''
		if(partial and definition.get('autocomplete_callback')):
			content = definition['autocomplete_callback'](req, partial, definition)
		
		app.raise200([('Content-Type', 'text/plain')], [content])
	
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return 'text/html; charset=UTF-8'
	
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return self.template
	
	
	def get_template_root(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template_root()}
		"""
		return select_template_root(self.get_template(req))


