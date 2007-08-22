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
from modu.util import form
from modu import persist

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


class AdminResource(resource.CheetahTemplateResource):
	def __init__(self, path='/admin', **options):
		self.path = path
		self.options = options
	
	def get_paths(self):
		return [self.path]
	
	def prepare_content(self, req):
		user = req['modu.user']
		if(user and user.get_id()):
			if(req.app.tree.postpath[0] == 'detail'):
				self.prepare_detail(req)
			else:
				self.prepare_listing(req)
		else:
			self.prepare_login(req)
	
	def prepare_login(self, req):
		self.template = 'login.html.tmpl'
		
		login_form = form.FormNode('login')
		login_form['username'](type='textfield', label='Username')
		login_form['password'](type='password', label='Password')
		login_form['submit'](type='submit', value='login')
		login_form.validate = validate_login
		login_form.submit = submit_login
		
		login_form.execute(req)
		
		self.set_slot('login_form', login_form.render(req))
	
	def prepare_listing(self, req):
		self.template = 'listing.html.tmpl'
	
	def prepare_detail(self, req):
		self.template = 'detail.html.tmpl'
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return self.template


