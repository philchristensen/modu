# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

from modu.web import resource, user, app
from trac.web import main
from trac.web.api import HTTPForbidden

class Resource(resource.WSGIPassthroughResource):
	def __init__(self):
		super(Resource, self).__init__(main.dispatch_request)
	
	def prepare_content(self, req):
		path_info = req['PATH_INFO']
		if(path_info.startswith('/trac')):
			req['PATH_INFO'] = path_info[5:]
		elif(path_info.startswith('trac')):
			req['PATH_INFO'] = path_info[4:]
		
		req['SCRIPT_NAME'] = '/trac'
		
		req['REMOTE_USER'] = 'anonymous'
		if(req.user.get_id()):
			req['REMOTE_USER'] = req.user.username
		
		try:
			super(Resource, self).prepare_content(req)
		except HTTPForbidden, e:
			req.messages.report('message', "Sorry, Trac won't let you in: %s" % e.detail)
			req.session['auth_redirect'] = req.get_path(req.path)
			app.redirect(req.get_path('trac/login'))

class LoginSupportResource(resource.CheetahTemplateResource):
	def prepare_content(self, req):
		if(req.prepath[-1] == 'login'):
			login_form = user.get_default_login_form()
			if(login_form.execute(req)):
				if(req.user.get_id()):
					app.redirect(req.session.get('auth_redirect', req.get_path('/trac')))
				else:
					req.messages.report('error', "Sorry, that login was incorrect.")
			else:
				if('auth_redirect' not in req.session):
					req.session['auth_redirect'] = req.get('HTTP_REFERER', req.get_path('/trac'))
			
			self.set_slot('login_form', login_form.render(req))
			self.set_slot('title', 'modu: login')
		else:
			req.session.set_user(None)
			app.redirect(req.get('HTTP_REFERER', req.get_path('/trac')))
	
	def get_template(self, req):
		return 'login.html.tmpl'