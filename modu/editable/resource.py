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

import os.path, copy, re, datetime

from modu import util
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
	
	template_root = os.path.join(req.approot, 'template')
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
		self.content_type = 'text/html; charset=UTF-8'
	
	
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
		req.content.report('header', tags.style(type="text/css")[
			"@import '%s';" % req.get_path('assets', 'admin-styles.css')
		])
		
		user = req['modu.user']
		if(user and user.get_id()):
			if(req.prepath[-1] == 'logout'):
				req.session.set_user(None)
				if('auth_redirect' in req.session):
					del req.session['auth_redirect']
				app.redirect(req.get_path(self.path))
			
			itemdefs = define.get_itemdefs()
			
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
		
		login_form = user.get_default_login_form()
		
		login_form.execute(req)
		
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
		
		query_data = form.NestedFieldStorage({'QUERY_STRING':req.get('QUERY_STRING', ''),
												'wsgi.input':req['wsgi.input']})
		
		# create a fake storable to make itemdef/form happy
		search_storable = storable.Storable(table_name)
		# give it a factory so fields can use its store reference
		search_storable.set_factory(req.store.get_factory(table_name))
		# build the form tree
		search_form = itemdef.get_search_form(req, search_storable)
		# get any saved search data
		session_search_data = req.session.setdefault('search_form', {}).setdefault(itemdef.name, {})
		
		order_by = itemdef.config.get('order_by', 'id DESC')
		if('order' in query_data and re.match(r'^\w+$', query_data['order'].value)):
			order_by = query_data['order'].value
			if('desc' in query_data and query_data['desc'].value):
				order_by += ' DESC'
		ordering_dict = {'__order_by':order_by}
		
		limits = None
		
		if(search_form.execute(req)):
			search_data = search_form.data[search_form.name]
			if('clear_search' in search_data):
				req.session.setdefault('search_form', {})[itemdef.name] = {}
				app.redirect(req.get_path(self.path, 'listing', table_name))
			
			for submit in search_form.find_submit_buttons():
				search_data.pop(submit.name, None)
			
			data = {}
			data.update(ordering_dict)
			for key, value in search_data.items():
				result = itemdef[key].get_search_value(value.value)
				session_search_data[key] = value.value
				key = itemdef[key].get('column', key)
				if(result is not None and result is not ''):
					if(isinstance(result, dict)):
						for k, v in result.items():
							data[k] = v
					else:
						data[key] = result
			#print 'post: %s' % data
		elif(session_search_data):
			search_data = {search_form.name:session_search_data}
			search_form.load_data(req, search_data)
			
			data = {}
			data.update(ordering_dict)
			for key, value in session_search_data.items():
				result = itemdef[key].get_search_value(value)
				key = itemdef[key].get('column', key)
				if(result is not None):
					if(isinstance(result, dict)):
						for k, v in result.items():
							data[k] = v
					else:
						data[key] = result
			#print 'session: %s' % data
		else:
			#print 'default: %s' % ordering_dict
			data = ordering_dict
		
		template_variable_callback = itemdef.config.get('template_variable_callback')
		if(callable(template_variable_callback)):
			for key, value in template_variable_callback(req, forms, search_storable).items():
				self.set_slot(key, value)
		
		if(req.postpath[0] == 'listing'):
			self.template = itemdef.config.get('list_template', 'admin-listing.html.tmpl')
			
			pager = page.Paginator()
			if('page' in query_data):
				pager.page = int(query_data['page'].value)
			else:
				pager.page = 1
			pager.per_page = itemdef.config.get('per_page', 25)
			
			items = pager.get_results(req.store, table_name, data)
			forms = itemdef.get_listing(req, items)
			thm = theme.Theme(req)
			
			self.set_slot('pager', pager)
			self.set_slot('search_form', search_form.render(req))
			self.set_slot('page_guide', thm.page_guide(pager, req.get_path(req.path)))
			self.set_slot('forms', forms)
			self.set_slot('theme', thm)
			self.set_slot('selected_items', items)
			
			default_title = 'Listing %s Records' % itemdef.name.title()
			custom_title = itemdef.config.get('listing_title', default_title)
			self.set_slot('title', tags.encode_htmlentities(custom_title))
		elif(req.postpath[0] == 'export'):
			if(callable(itemdef.config.get('export_query_builder'))):
				data = itemdef.config['export_query_builder'](req, itemdef, data)
			items = req.store.load(table_name, data)
			self.prepare_export(req, itemdef, items)
	
	
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
	
	
	def prepare_custom(self, req, itemdef):
		"""
		Manage use of custom resources in the admin interface.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@param itemdef: an itemdef with custom resource info
		@type itemdef: L{modu.editable.define.itemdef}
		"""
		rsrc = itemdef.config.get('resource')
		if not(rsrc):
			app.raise404('There is no resource at the path: %s' % req['REQUEST_URI'])
		if not(isinstance(rsrc, resource.CheetahTemplateContent)):
			app.raise500('The resource at %s is invalid.' % req['REQUEST_URI'])
		
		self.template = rsrc.get_template(req)
		self.content_type = rsrc.get_content_type(req)
		
		rsrc.prepare_content(req)
		for slot in rsrc.get_slots():
			self.set_slot(slot, rsrc.get_slot(slot))
	
	
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
	
	
	def get_template_root(self, req, template=None):
		"""
		@see: L{modu.web.resource.ITemplate.get_template_root()}
		"""
		if(template is None):
			template = self.get_template(req)
		
		return select_template_root(req, template)
	


class ACLResource(resource.CheetahTemplateResource):
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
		        resource        = resource.ACLResource()
		    )
		)
	
	
	"""
	def get_paths(self):
		"""
		@see: L{modu.web.resource.IResource.get_paths()}
		"""
		return ['/acl']
	
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		form_data = form.NestedFieldStorage(req)
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
