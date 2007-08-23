# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains resources for configuring a default admin interface.
"""

import os.path

from modu.web import resource, app, user
from modu.editable import define
from modu.util import form, theme, tags
from modu import persist
from modu.persist import page

def validate_login(req, form):
	if not(form.data[form.name]['username']):
		form.set_form_error('username', "Please enter your username.")
	if not(form.data[form.name]['password']):
		form.set_form_error('password', "Please enter your password.")
	return not form.has_errors()
	

def submit_login(req, form):
	req.store.ensure_factory('user', user.User)
	form_data = form.data[form.name]
	encrypt_sql = persist.interp(' = ENCRYPT(%s, SUBSTRING(crypt, 1, 2))', [form_data['password'].value])
	u = req.store.load_one('user', username=form_data['username'].value, crypt=persist.RAW(encrypt_sql))
	req.session.set_user(u)


def configure_store(req, itemdef):
	table_name = itemdef.config.get('table', itemdef.name)
	if('factory' in itemdef.config):
		req.store.register_factory(table_name, itemdef.config['factory'])
	elif('model_class' in itemdef.config):
		req.store.ensure_factory(table_name, itemdef.config['model_class'])
	else:
		req.store.ensure_factory(table_name)


class AdminResource(resource.CheetahTemplateResource):
	def __init__(self, path='/admin', **options):
		self.path = path
		self.options = options
	
	def get_paths(self):
		return [self.path]
	
	def prepare_content(self, req):
		user = req['modu.user']
		self.set_slot('user', user)
		if(user and user.get_id()):
			itemdefs = define.get_itemdefs()
			
			self.itemdef_layout = define.get_itemdef_layout(req.user, itemdefs)
			self.set_slot('itemdef_layout', self.itemdef_layout)
			
			if(len(req.app.tree.postpath) > 1):
				itemdef_name = req.app.tree.postpath[1]
				selected_itemdef = itemdefs.get(itemdef_name)
				self.set_slot('selected_itemdef', selected_itemdef)
				
				if(selected_itemdef):
					configure_store(req, selected_itemdef)
				
				if(req.app.tree.postpath[0] == 'detail'):
					self.prepare_detail(req, selected_itemdef)
				else:
					self.prepare_listing(req, selected_itemdef)
			else:
				app.raise404('There is no item list at the path: %s' % req['REQUEST_URI'])
		else:
			self.set_slot('itemdef_layout', None)
			self.set_slot('selected_itemdef', None)
			self.prepare_login(req)
	
	def prepare_login(self, req):
		self.template = 'login.html.tmpl'
		
		login_form = form.FormNode('login')
		login_form['username'](type='textfield', label='Username')
		login_form['password'](type='password', label='Password')
		login_form['submit'](type='submit', value='login')
		login_form.validate = validate_login
		login_form.submit = submit_login
		
		if(login_form.execute(req) and req.session.get_user()):
			self.prepare_listing(req, None)
		else:
			self.set_slot('login_form', login_form.render(req))
	
	def prepare_listing(self, req, itemdef):
		self.template = 'listing.html.tmpl'
		table_name = itemdef.config.get('table', itemdef.name)
		
		pager = page.Paginator()
		items = pager.get_results(req.store, table_name, {})
		forms = itemdef.get_listing(items, req.user)
		thm = ListingTheme(req)
		
		self.set_slot('items', items)
		self.set_slot('pager', pager)
		self.set_slot('form', thm.form(forms))
	
	def prepare_detail(self, req, itemdef):
		self.template = 'detail.html.tmpl'
		self.set_slot('form', None)
		if(len(req.app.tree.postpath) > 2):
			try:
				item_id = req.app.tree.postpath[2]
				table_name = itemdef.config.get('table', itemdef.name)
				selected_item = req.store.load_one(table_name, {'id':int(item_id)})
				
				frm = itemdef.get_form(selected_item, req.user)
				if('theme' in itemdef.config):
					frm.theme = itemdef.config['theme']
				self.set_slot('form', frm.render(req))
				self.set_slot('selected_item', selected_item)
			except TypeError:
				app.raise404('There is no detail view at the path: %s' % req['REQUEST_URI'])
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
		content = tags.table()[content]
		
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
	
	def form_element(self, form_id, element):
		return tags.td()[self._form_element(form_id, element)]
	
