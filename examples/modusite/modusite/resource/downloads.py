# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

import tempfile

try:
	from cStringIO import StringIO
except ImportError, e:
	from StringIO import StringIO

from modu.web import resource, app

from modusite.model import page, project

class DownloadsResource(resource.CheetahTemplateResource):
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		req.store.ensure_factory('page', page.Page, force=True)
		p = req.store.load_one('page', {'active':1, 'url_code':'downloads'})
		
		if(p is None):
			app.raise404(page_code)
		#/trac/changeset/HEAD/trunk?old_path=%2F&format=zip
		req.store.ensure_factory('project', project.Project, force=True)
		projects = req.store.load('project')
		
		self.set_slot('title', p.title)
		self.set_slot('projects', projects)
		self.content = p.data
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return 'text/html; charset=UTF-8'
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return self.content
	
	def get_template_type(self):
		return 'str'

