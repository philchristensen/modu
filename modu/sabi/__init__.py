# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import modu import web, wsgi
from modu.web import resource

class DynamicResource(resource.Resource):
	def __init__(self, content):
		if not(isinstance(content, resource.Content) or callable(content)):
			raise TypeError('content object must be callable or instance of resource.Content')
		self.content = content
	
	def get_paths(self):
		return paths
	
	def set_paths(self, paths):
		self.paths = paths
	
	def prepare_content(self, req):
		if(callable(self.content)):
			self._content = self.content(req)
		else:
			self.content.prepare_content(req)
	
	def get_content(self, req):
		if(hasattr(self, '_content')):
			return self._content
		else:
			return self.content.get_content(req)
	
	def get_content_type(self, req):
		if(hasattr(self, '_content')):
			return 'text/html'
		else:
			return self.content.get_content_type(req)


class ProtectedDynamicResource(DynamicResource):
	def prepare_content(self, req):
		if not(check_access(req)):
			raise web.HTTPStatus('403 Forbidden', [('Content-Type', 'text/html')], [wsgi.content403()])
		super(ProtectedDynamicResource, self).prepare_content(req)
	
	def set_perms(self, perms):
		self.perms = perms
	
	def check_access(self, req):
		return True
	
	