# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

from modu.web import resource, user, app
from trac.web import main

class Resource(resource.WSGIPassthroughResource):
	def __init__(self):
		super(Resource, self).__init__(['/trac'], main.dispatch_request)
	
	def prepare_content(self, req):
		req['PATH_INFO'] = req['PATH_INFO'].replace('trac', '')
		req['SCRIPT_NAME'] = '/trac'
		
		req['REMOTE_USER'] = 'anonymous'
		if(req.user.get_id()):
			req['REMOTE_USER'] = req.user.username
		super(Resource, self).prepare_content(req)

class LoginSupportResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/trac/login', '/trac/logout']
	
	def prepare_content(self, req):
		if(req.prepath[-1] == 'login'):
			login_form = user.get_default_login_form()
			login_form.execute(req)
			
			if(req.user.get_id()):
				app.redirect('/trac')
			
			self.set_slot('login_form', login_form.render(req))
			self.set_slot('title', 'modu: login')
		else:
			req.session.set_user(None)
			app.redirect('/trac')
	def get_template(self, req):
		return 'login.html.tmpl'