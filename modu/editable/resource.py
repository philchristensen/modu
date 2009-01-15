# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains resources for configuring a default admin interface.

All the content in this module and the contained classes should deal
only with itemdef organization and management. Any form- or validation-
specific code should go in L{modu.editable.define}.
"""

import os.path, copy, re, datetime, cgi

from modu import util, web
from modu.web import resource, app, user
from modu.editable import define
from modu.util import form, theme, tags, csv
from modu.persist import page, storable, sql

def select_template_root(req, template):
	"""
	Determine the appropriate directory to find the provided template.
	
	This is used by the Cheetah template code to allow for default templates
	to be included with the modu distribution.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param template: the template about to be opened
	@type template: str
	
	@return: path to template directory
	@rtype: str
	"""
	import modu
	
	if(hasattr(req.resource, 'template_dir')):
		template_root = req.resource.template_dir
	else:
		template_root = getattr(req.app, 'template_dir', os.path.join(req.approot, 'template'))
	
	if(os.access(os.path.join(template_root, template), os.F_OK)):
		return template_root
	
	return os.path.join(os.path.dirname(modu.__file__), 'assets', 'default-template')


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
		req.store.ensure_factory(table_name, itemdef.config['model_class'], force=True)
	else:
		req.store.ensure_factory(table_name)

class CustomRequestWrapper(object):
	"""
	This modifies the request object when used with custom admin interfaces.
	"""
	def __init__(self, req):
		self._req = req
	
	def __getattr__(self, key):
		if(key == 'prepath'):
			return self._req.prepath + self._req.postpath[0:2]
		elif(key == 'postpath'):
			return self._req.postpath[2:]
		return getattr(self._req, key)
	
	def __getitem__(self, key):
		return self._req[key]
	
	def __setitem__(self, key, value):
		self._req[key] = value
	
	def __contains__(self, key):
		return key in self._req

class AdminTemplateResourceMixin(object):
	def get_template_root(self, req, template=None):
		"""
		@see: L{modu.web.resource.ITemplate.get_template_root()}
		"""
		if(template is None):
			template = self.get_template(req)
		
		return select_template_root(req, template)


class AdminResource(AdminTemplateResourceMixin, resource.CheetahTemplateResource):
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
	def __init__(self, **options):
		"""
		Create an instance of the admin tool.
		
		@param path: The path this instance should respond to.
		@type path: str
		"""
		self.options = options
		if('template_dir' in options):
			self.template_dir = options['template_dir']
		self.content_type = 'text/html; charset=UTF-8'
	
	
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		req.content.report('header', tags.style(type="text/css")[
			"@import '%s';" % req.get_path('assets', 'admin-styles.css')
		])
		
		user = req['modu.user']
		if(user and user.get_id()):
			if(req.postpath and req.postpath[0] == 'logout'):
				req.session.set_user(None)
				if('auth_redirect' in req.session):
					del req.session['auth_redirect']
				app.redirect(req.get_path(req.prepath))
			
			itemdefs = define.get_itemdefs(itemdef_module=self.options.get('itemdef_module', None))
			
			# get_itemdef_layout adds some data and clones the itemdef
			self.itemdef_layout = define.get_itemdef_layout(req, itemdefs)
			
			# FIXME: This is inelegant -- we find the current itemdef
			# by using itemdefs.get(req.postpath[1]), so we recreate
			# the itemdef list from the itemdef layout to stop
			# malicious URL access.
			# TODO: Limit the itemdefs by user *first*, then modify
			# get_itemdef_layout() to organize, but not limit.
			if(self.itemdef_layout):
				itemdefs = dict([(itemdef.name, itemdef) for itemdef in
									reduce(lambda x, y: x+y, self.itemdef_layout.values())])
			else:
				itemdefs = {}
			
			self.set_slot('itemdef_layout', self.itemdef_layout)
			
			if(len(req.postpath) > 1):
				itemdef_name = req.postpath[1]
				# we just need to select the right itemdef
				selected_itemdef = itemdefs.get(itemdef_name)
				
				self.set_slot('selected_itemdef', selected_itemdef)
				
				if(selected_itemdef is not None):
					configure_store(req, selected_itemdef)
					
					if(req.postpath[0] == 'detail'):
						self.prepare_detail(req, selected_itemdef)
					elif(req.postpath[0] == 'autocomplete'):
						self.prepare_autocomplete(req, selected_itemdef)
					elif(req.postpath[0] == 'custom'):
						self.prepare_custom(req, selected_itemdef)
					elif(req.postpath[0] in ('listing', 'export')):
						self.prepare_listing(req, selected_itemdef)
					else:
						app.raise404()
				else:
					app.raise403()
			else:
				default_path = self.options.get('default_path')
				if(callable(default_path)):
					default_path = default_path(req)
				if(default_path):
					redirect_path = req.get_path(default_path)
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
		
		login_form = user.get_default_login_form()
		
		if(login_form.execute(req)):
			app.redirect(req.get_path(req.path))
		
		self.set_slot('login_form', login_form.render(req))
		self.set_slot('title', self.options.get('login_title', 'admin login'))
	
	
	def prepare_listing(self, req, itemdef):
		"""
		Handle creation and display of the listing page.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to use to generate the listing
		@type itemdef: L{modu.editable.define.itemdef}
		"""
		table_name = itemdef.config.get('table', itemdef.name)
		session_search_data = req.session.setdefault('search_form', {}).setdefault(itemdef.name, {})
		
		form_data = req.data.get('%s-search-form' % itemdef.name, {})
		if(isinstance(form_data, dict) and form_data.get('clear_search', '')):
			req.session.setdefault('search_form', {})[itemdef.name] = {}
			app.redirect(req.get_path(req.prepath, 'listing', itemdef.name))
		
		# create a fake storable to make itemdef/form happy
		search_storable = storable.Storable(table_name)
		if('default_search' in itemdef.config):
			for k, v in itemdef.config['default_search'].items():
				k = itemdef[k].get_column_name()
				setattr(search_storable, k, v)
		if(session_search_data):
			for k, v in session_search_data.items():
				if(k in itemdef):
					k = itemdef[k].get_column_name()
				setattr(search_storable, k, v)
		
		# give it a factory so fields can use its store reference
		search_storable.set_factory(req.store.get_factory(table_name))
		# build the form tree
		search_form = itemdef.get_search_form(req, search_storable)
		# this will make sure that if we're on a page other than 1,
		# a search submission will take us back to page 1
		search_form(action=req.get_path(req.path))
		
		order_by = itemdef.config.get('order_by', 'id DESC')
		if('order' in req.data and re.match(r'^\w+$', req.data['order'].value)):
			order_by = req.data['order'].value
			if('desc' in req.data and req.data['desc'].value):
				order_by += ' DESC'
		
		search_attribs = {'__order_by':order_by}
		#search_attribs.update(itemdef.config.get('default_where', {}))
		
		# this function will call search_form.execute()
		search_params = self.get_search_params(req, itemdef, search_form)
		search_attribs.update(search_params)
		
		if(req.postpath[0] == 'listing'):
			pager = page.Paginator()
			if('page' in req.data):
				pager.page = int(req.data['page'].value)
			else:
				pager.page = 1
			pager.per_page = itemdef.config.get('per_page', 25)
			
			items = pager.get_results(req.store, table_name, search_attribs)
			forms = itemdef.get_listing(req, items)
			thm = theme.Theme(req)
			
			if(len(search_form)):
				self.set_slot('search_form', search_form.render(req))
			else:
				self.set_slot('search_form', '')
			
			self.set_slot('pager', pager)
			self.set_slot('page_guide', thm.page_guide(pager, req.get_path(req.path)))
			self.set_slot('forms', forms)
			self.set_slot('theme', thm)
			self.set_slot('selected_items', items)
			
			default_title = 'Listing %s Records' % itemdef.name.title()
			custom_title = itemdef.config.get('listing_title', default_title)
			self.set_slot('title', tags.encode_htmlentities(custom_title))
			
			template_variable_callback = itemdef.config.get('template_variable_callback')
			if(callable(template_variable_callback)):
				for key, value in template_variable_callback(req, forms, search_storable).items():
					self.set_slot(key, value)
			
			self.template = itemdef.config.get('list_template', 'admin-listing.html.tmpl')
		elif(req.postpath[0] == 'export'):
			if(callable(itemdef.config.get('export_query_builder'))):
				data = itemdef.config['export_query_builder'](req, itemdef, data)
			items = req.store.load(table_name, data)
			self.prepare_export(req, itemdef, items)
	
	def get_search_params(self, req, itemdef, search_form):
		"""
		Get a dictionary of search parameter.
		
		Take into consideration previous searches saved in session.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to use to generate the listing
		@type itemdef: L{modu.editable.define.itemdef}
		
		@param search_form: the search form, in case any custom fields need it
		@type search_form: L{modu.util.form.FormNode}
		"""
		# get any saved search data
		session_search_data = req.session.setdefault('search_form', {}).setdefault(itemdef.name, {})
		data = {}
		
		if(session_search_data):
			search_data = {search_form.name:session_search_data}
			search_form.load_data(req, search_data)
			
			for key, value in session_search_data.items():
				if(key in itemdef):
					cgi_value = cgi.MiniFieldStorage(key, value)
					result = itemdef[key].get_search_value(cgi_value, req, search_form)
				else:
					result = value
				if(result is not None):
					if(isinstance(result, dict)):
						for k, v in result.items():
							data[k] = v
					else:
						if(key in itemdef):
							key = itemdef[key].get_column_name()
						data[key] = result
			#print 'session: %s' % data
		
		if(not session_search_data or search_form.execute(req)):
			data = {}
			
			submit_buttons = search_form.find_submit_buttons()
			
			for key, field in search_form.items():
				if(key not in itemdef):
					continue
				
				result = itemdef[key].get_search_value(field, req, search_form)
				value = getattr(field, 'value', None)
				if(value):
					session_search_data[key] = value
				
				key = itemdef[key].get_column_name()
				if(result is not None):
					if(isinstance(result, dict)):
						for k, v in result.items():
							data[k] = v
					else:
						data[key] = result
			#print 'post: %s' % data
		
		if('default_where' in itemdef.config):
			result = itemdef.config['default_where']
			data.update(result)
		
		return data
	
	def prepare_export(self, req, itemdef, items):
		"""
		Manage creation of an export file.
		
		The selected items will be escaped and formatted as
		either tab- or comma-separated values.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to use to generate the export
		@type itemdef: L{modu.editable.define.itemdef}
		
		@param items: the items returned by the search result.
		@type items: list(L{modu.persist.storable.Storable})
		"""
		header_string = None
		
		le = itemdef.config.get('export_le', '\n')
		export_type = itemdef.config.get('export_type', 'csv')
		
		export_formatter = self.prepare_standard_export
		if(callable(itemdef.config.get('export_formatter'))):
			export_formatter = itemdef.config['export_formatter']
		
		rows = [export_formatter(req, itemdef, item) for item in items]
		
		export_callback = itemdef.config.get('export_callback')
		if(callable(export_callback)):
			export_callback(req)
		
		if(export_type == 'csv'):
			self.content_type = 'text/csv; charset=UTF-8'
			self.content = csv.generate_csv(rows, le)
			ext = 'csv'
		elif(export_type == 'tsv'):
			self.content_type = 'text/tsv; charset=UTF-8'
			self.content = csv.generate_tsv(rows, le)
			ext = 'txt'
		else:
			raise RuntimeError("Invalid export type '%s'" % export_type)
		
		export_filename = '%s_%s.%s' % (itemdef.name, datetime.datetime.now().strftime('%Y-%m-%d_%H%M'), ext)
		export_size = len(self.content)
		req.add_header('Content-Disposition', 'attachment; filename=%s; size=%d' % (export_filename, export_size))
	
	
	def prepare_standard_export(self, req, itemdef, item):
		"""
		Create a row for an export file.
		
		The default behavior is to attempt to generate an export
		row using the labels and list output of the current itemdef.
		
		This can be problematic, since some list-view items are quite
		expensive when used across the entire result set.
		
		Itemdefs can override 'export_formatter' to change the functionality
		of this method.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: the itemdef to use to generate the export
		@type itemdef: L{modu.editable.define.itemdef}
		
		@param item: the item to export.
		@type item: L{modu.persist.storable.Storable}
		"""
		result = util.OrderedDict()
		for name, field in itemdef.items():
			if(field.get('listing', False)):
				frm = field.get_element(req, 'listing', item)
				
				header = field.get('label', name)
				value = frm.attributes.get('value', getattr(item, field.get_column_name(), None))
				
				formatter = field.get('export_formatter', None)
				if(callable(formatter)):
					value = formatter(value)
				
				result[header] = value
		return result
	
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
				if(itemdef.config.get('no_create')):
					app.raise403('Sorry, record creation is turned off for this itemdef.')
				
				if('model_class' in itemdef.config):
					selected_item = itemdef.config['model_class']()
				else:
					selected_item = storable.Storable(table_name)
				
				# Populate the new item if necessary
				if('__init__' in req.data):
					for k, v in req.data['__init__'].items():
						setattr(selected_item, k, v.value)
				
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
				# this is technically only necessary if errors are reported
				# on form items but they do not prevent completion (e.g., return False)
				new_frm.errors = frm.errors
				frm = new_frm
			else:
				# If we haven't submitted the form, errors should definitely be empty
				for field, errs in frm.get_errors().items():
					for err in errs:
						err = tags.a(href="#form-item-%s" % field)[err]
						req.messages.report('error', '%s: %s' % (field, err))
			
			template_variable_callback = itemdef.config.get('template_variable_callback')
			if(callable(template_variable_callback)):
				result = template_variable_callback(req, frm, selected_item)
				if(isinstance(result, dict)):
					for key, value in result.items():
						self.set_slot(key, value)
			
			self.set_slot('form', frm)
			self.set_slot('theme', frm.get_theme(req))
			self.set_slot('selected_item', selected_item)
			
			if('title_column' in itemdef.config and item_id != 'new'):
				item_name = "'%s'" % getattr(selected_item, itemdef.config['title_column'])
			else:
				item_name = '#' + str(selected_item.get_id())
			default_title = 'Details for %s %s' % (itemdef.name.title(), item_name)
			custom_title = itemdef.config.get('detail_title', default_title)
			self.set_slot('title', tags.encode_htmlentities(custom_title))
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
		post_data = req.data
		results = []
		
		if('q' in post_data):
			partial = post_data['q'].value
		else:
			partial = None
		
		content = ''
		if(partial and definition.get('autocomplete_callback')):
			content = definition['autocomplete_callback'](req, partial, definition)
		
		app.raise200([('Content-Type', 'text/plain')], [content])
	
	
	def prepare_custom(self, req, itemdef):
		"""
		Manage use of custom resources in the admin interface.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: an itemdef with custom resource info
		@type itemdef: L{modu.editable.define.itemdef}
		"""
		result = itemdef.config.get('resource')
		
		if(isinstance(result, (list, tuple))):
			rsrc_class, args, kwargs = result
		else:
			rsrc_class = result
			args = []
			kwargs = {}
		
		if not(rsrc_class):
			app.raise404('There is no resource at the path: %s' % req['REQUEST_URI'])
		if not(resource.ITemplate.implementedBy(rsrc_class)):
			app.raise500('The resource at %s is invalid, it must be an ITemplate implementor.' % req['REQUEST_URI'])
		
		rsrc = rsrc_class(*args, **kwargs)
		req['modu.resource'] = rsrc
		
		for key in self.get_slots():
			rsrc.set_slot(key, self.get_slot(key))
		
		content = rsrc.get_response(req)
		raise web.HTTPStatus('200 OK', req.get_headers(), content)
	
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return self.content_type
	
	
	def get_content(self, req):
		"""
		Allow for content override (used by export).
		
		Normally, this function just calls the superclass, but if
		C{self.content} exists, that value is returned instead.
		
		@see: L{modu.web.resource.IContent.get_content()}
		"""
		if(hasattr(self, 'content')):
			return self.content
		else:
			return super(AdminResource, self).get_content(req)
	
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return self.template


class ACLResource(AdminTemplateResourceMixin, resource.CheetahTemplateResource):
	"""
	A convenience resource for managing ACLs.
	
	Sample Itemdef::
		from modu.editable import define, resource
		
		__itemdef__ = define.itemdef(
		    __config            = dict(
		        name            = 'acl',
		        label           = 'access control',
		        category        = 'accounts',
		        acl             = 'access admin',
		        weight          = -10,
		        resource        = resource.ACLResource
		    )
		)
	
	
	"""
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		form_data = req.data
		if('new' in form_data):
			new_data = form_data['new']
			if('permission' in new_data):
				req.store.ensure_factory('permission')
				p = storable.Storable('permission')
				p.name = new_data['permission'].value
				req.store.save(p)
			elif('role' in new_data):
				req.store.ensure_factory('role')
				r = storable.Storable('role')
				r.name = new_data['role'].value
				req.store.save(r)
		
		permission_query = "SELECT id, name FROM permission ORDER BY name"
		result = req.store.pool.runQuery(permission_query)
		permissions = util.OrderedDict([(item['id'], item['name']) for item in result])
		
		role_query = "SELECT id, name FROM role ORDER BY name"
		result = req.store.pool.runQuery(role_query)
		roles = util.OrderedDict([(item['id'], item['name']) for item in result])
		
		if('acl' in form_data):
			acl_data = form_data['acl']
			checked = []
			unchecked = []
			for pid in permissions.keys():
				pid = str(pid)
				for rid in roles.keys():
					rid = str(rid)
					if(pid in acl_data and rid in acl_data[pid]):
						checked.append({'role_id':rid, 'permission_id':pid})
					else:
						unchecked.append({'role_id':rid, 'permission_id':pid})
			
			for perm in checked:
				replace_query = sql.build_replace('role_permission', perm)
				req.store.pool.runOperation(replace_query)
			
			for perm in unchecked:
				delete_query = sql.build_delete('role_permission', perm)
				req.store.pool.runOperation(delete_query)
		
		acl_query = """SELECT * FROM role_permission"""
		acl_results = req.store.pool.runQuery(acl_query)
		acl_map = {}
		for item in acl_results:
			acl_map.setdefault(item['permission_id'], []).append(item['role_id'])
		
		self.set_slot('permissions', permissions)
		self.set_slot('roles', roles)
		self.set_slot('acl_map', acl_map)
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return 'admin-acl.html.tmpl'
