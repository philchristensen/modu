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
from modu import persist
from modu.persist import page, storable

def validate_login(req, form):
	if not(form.data[form.name]['username']):
		form.set_form_error('username', "Please enter your username.")
	if not(form.data[form.name]['password']):
		form.set_form_error('password', "Please enter your password.")
	return not form.has_errors()
	

def submit_login(req, form):
	req.store.ensure_factory('user', user.User)
	form_data = form.data[form.name]
	encrypt_sql = persist.interp('%%s = ENCRYPT(%s, SUBSTRING(crypt, 1, 2))', [form_data['password'].value])
	u = req.store.load_one('user', username=form_data['username'].value, crypt=persist.RAW(encrypt_sql))
	if(u):
		req.session.set_user(u)
	else:
		req.messages.report('error', "Sorry, that login was incorrect.")


def configure_store(req, itemdef):
	table_name = itemdef.config.get('table', itemdef.name)
	if('factory' in itemdef.config):
		req.store.register_factory(table_name, itemdef.config['factory'])
	elif('model_class' in itemdef.config):
		req.store.ensure_factory(table_name, itemdef.config['model_class'])
	else:
		req.store.ensure_factory(table_name)


class AdminResource(resource.CheetahTemplateResource):
	def __init__(self, path=None, **options):
		if(path is None):
			path = '/admin'
		self.path = path
		self.options = options
	
	def get_paths(self):
		return [self.path, '%s/logout' % self.path]
	
	def prepare_content(self, req):
		user = req['modu.user']
		self.set_slot('user', user)
		if(user and user.get_id()):
			if(req.app.tree.prepath[-1] == 'logout'):
				req.session.set_user(None)
				app.redirect(req.get_path(self.path))
			
			itemdefs = define.get_itemdefs()
			
			# get_itemdef_layout adds some data and clones the itemdef
			self.itemdef_layout = define.get_itemdef_layout(req, itemdefs)
			
			# FIXME: This is inelegant -- we need to get at the cloned itemdef
			# as it already has some config data in it (because of get_itemdef_layout)
			itemdefs = dict([(itemdef.name, itemdef) for itemdef in
								reduce(lambda x, y: x+y, self.itemdef_layout.values())])
			
			self.set_slot('itemdef_layout', self.itemdef_layout)
			
			if(len(req.app.tree.postpath) > 1):
				itemdef_name = req.app.tree.postpath[1]
				# we just need to select the right itemdef
				selected_itemdef = itemdefs.get(itemdef_name)
				
				self.set_slot('selected_itemdef', selected_itemdef)
				
				if(selected_itemdef):
					configure_store(req, selected_itemdef)
					
					if(req.app.tree.postpath[0] == 'detail'):
						self.prepare_detail(req, selected_itemdef)
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
		self.template = 'admin-listing.html.tmpl'
		table_name = itemdef.config.get('table', itemdef.name)
		
		query_data = form.NestedFieldStorage(req)
		pager = page.Paginator()
		if('page' in query_data):
			pager.page = int(query_data['page'].value)
		else:
			pager.page = 1
		pager.per_page = itemdef.config.get('per_page', 25)
		
		search_storable = storable.Storable(table_name)
		search_storable.set_factory(req.store.get_factory(table_name))
		search_form = itemdef.get_search_form(search_storable, req.user)
		if(search_form.execute(req)):
			search_data = search_form.data[search_form.name]
			for submit in search_form.find_submit_buttons():
				search_data.pop(submit.name, None)
			data = form.FieldStorageDict(search_data)
			items = pager.get_results(req.store, table_name, data)
		else:
			items = pager.get_results(req.store, table_name, {})
		
		forms = itemdef.get_listing(items, req.user)
		thm = ListingTheme(req)
		
		self.set_slot('items', items)
		self.set_slot('pager', pager)
		self.set_slot('search_form', search_form.render(req))
		self.set_slot('page_guide', thm.page_guide(pager, req.get_path(req.path)))
		self.set_slot('form', thm.form(forms))
	
	def prepare_detail(self, req, itemdef):
		self.template = 'admin-detail.html.tmpl'
		self.set_slot('form', None)
		if(len(req.app.tree.postpath) > 2):
			item_id = req.app.tree.postpath[2]
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
			
			frm = itemdef.get_form(selected_item, req.user)
			if('theme' in itemdef.config):
				frm.theme = itemdef.config['theme']
			
			if(frm.execute(req)):
				# we regenerate the form because some fields don't know their
				# value until after the form is saved (e.g., postwrite fields)
				new_frm = itemdef.get_form(selected_item)
				new_frm.errors = frm.errors
				frm = new_frm
			else:
				# If we haven't submitted the form, errors should definitely be empty
				for field, err in frm.errors.items():
					req.messages.report('error', err)
			
			self.set_slot('form', frm.render(req))
			self.set_slot('selected_item', selected_item)
		else:
			app.raise404('There is no detail view at the path: %s' % req['REQUEST_URI'])
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return self.template


class ListingTheme(theme.Theme):
	def form(self, form_list):
		content = ''
		for form in form_list:
			row = ''
			if not(content):
				content = ''.join([str(tags.th()[form[child].attrib('label', form[child].name)]) for child in form])
			for child in form:
				row += self.form_element(form.name, form[child])
			content += tags.tr()[row]
		content = tags.table(_id='listing-table')[content]
		
		if(len(form_list)):
			form = form_list[0]
			attribs = form.attrib('attributes', {})
			attribs['name'] = form.name.replace('-', '_')
			attribs['id'] = form.name
			attribs['enctype'] = form.attrib('enctype', 'application/x-www-form-urlencoded')
			attribs['method'] = form.attrib('method', 'post')
		
			action = form.attrib('action', None)
			if(action):
				attribs['action'] = action
			return tags.form(**attribs)["\n" + content]
		
		return tags.form()["\n" + content]
	
	def form_element(self, form_id, element):
		return tags.td()[self._form_element(form_id, element)]
	
