# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#

from modu.web import resource, user, app
from modu.util import auth

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
		
		if(req.user.get_id()):
			req['REMOTE_USER'] = req.user.username
		else:
			req['REMOTE_USER'] = 'anonymous'
		
		try:
			super(Resource, self).prepare_content(req)
		except HTTPForbidden, e:
			app.raise403(str(e))

class LoginSupportResource(resource.Resource):
	def get_response(self, req):
		if(auth.has_basic(req)):
			user = auth.verify_basic(req)
			req.session.set_user(user)
		else:
			auth.request_basic(req)
		
		referrer = req.get('HTTP_REFERER')
		if not(referrer):
			referrer = req.get_path('/trac')
		app.redirect(referrer)
