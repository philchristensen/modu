# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

from modu.web import resource
from trac.web import main

class Resource(resource.WSGIPassthroughResource):
	def __init__(self):
		super(Resource, self).__init__(['/trac'], main.dispatch_request)
	
	def prepare_content(self, req):
		#print req
		req['PATH_INFO'] = req['PATH_INFO'].replace('trac', '')
		req['SCRIPT_NAME'] = '/trac'
		
		req['REMOTE_USER'] = 'anonymous'
		if(req.user.get_id()):
			req['REMOTE_USER'] = req.user.username
		super(Resource, self).prepare_content(req)