# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu.web import resource, app

from modusite.model import blog

class Resource(resource.CheetahTemplateResource):
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		if not(req.postpath):
			app.redirect(req.get_path('/'))
		
		try:
			blog_id = int(req.postpath[0])
		except ValueError:
			app.redirect(req.get_path('/'))
		
		req.store.ensure_factory('blog', blog.Blog, force=True)
		b = req.store.load_one('blog', {'active':1, 'id':blog_id})
		
		if(b is None):
			app.raise404(blog_id)
		
		self.set_slot('title', b.title)
		self.set_slot('blog', b)
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return 'text/html; charset=UTF-8'
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return 'blog-detail.html.tmpl'

