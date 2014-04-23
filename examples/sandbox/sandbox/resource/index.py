# Modu Sandbox
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

from modu.web import resource, app

from sandbox.model import page

class Resource(resource.CheetahTemplateResource):
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		if not(req.postpath):
			self.set_slot('content', 'Welcome to your new project...')
			return
		
		page_code = req.postpath[0]
		
		req.store.ensure_factory('page', page.Page, force=True)
		p = req.store.load_one('page', {'active':1, 'url_code':page_code})
		
		if(p is None):
			app.raise404(page_code)
		
		self.set_slot('content', p.data)
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return 'text/html; charset=UTF-8'
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return 'index.html.tmpl'

