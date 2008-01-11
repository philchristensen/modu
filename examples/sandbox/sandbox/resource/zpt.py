# Modu Sandbox
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import resource

class Resource(resource.ZPTemplateResource):
	def get_paths(self):
		return ['/zpt']
	
	def prepare_content(self, req):
		self.set_slot('title', 'modu ZPT example page')
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'zpt.html.tmpl' 
