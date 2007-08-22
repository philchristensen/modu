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

from modu.web import resource, app
from modu.util import form

class AdminResource(resource.CheetahTemplateResource):
	def __init__(self, path='/admin', **options):
		self.path = path
		self.options = options
	
	def get_paths(self):
		return [self.path]
	
	def prepare_content(self, req):
		if(req['modu.user'] and req['modu.user'].get_id()):
			if(req.app.tree.postpath[0] == 'listing'):
				self.prepare_listing(req)
			elif(req.app.tree.postpath[0] == 'detail'):
				self.prepare_detail(req)
			else:
				app.redirect(os.path.join(req.app.base_path, req.path[1:]))
		else:
			self.prepare_login(req)
	
	def prepare_login(self, req):
		self.template = 'login.html.tmpl'
		
		
	
	def prepare_listing(self, req):
		self.template = 'listing.html.tmpl'
	
	def prepare_detail(self, req):
		self.template = 'detail.html.tmpl'
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return self.template


