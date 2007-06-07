# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.config import handler
from dathomir import config, resource

import os

class RootResource(resource.ZPTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		self.add_slot('title', 'Dathomir ZPT Test Page')
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

config.base_path = '/dathomir/examples/zpt'
config.db_url = None
config.session_class = None
config.initialize_store = False
config.activate(RootResource())
