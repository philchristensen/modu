# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
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

class Resource(resource.CheetahTemplateResource):
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		req.store.ensure_factory('page', page.Page, force=True)
		
		req.store.ensure_factory('project', project.Project, force=True)
		projects = req.store.load('project')
		
		self.set_slot('title', 'modu: downloads')
		self.set_slot('projects', projects)
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return 'text/html; charset=UTF-8'
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return 'downloads.html.tmpl'
		#return self.content

	def get_template_type(self):
		return 'filename'
		#return 'str'

