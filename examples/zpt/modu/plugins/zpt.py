# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id: ModuConfig.py 306 2007-07-01 04:45:48Z phil $
#
# See LICENSE for details

from modu.web.modpython import handler
from modu.web import app, resource

from modu.web.app import ISite
from zope.interface import classProvides
from twisted import plugin

import os

class RootResource(resource.ZPTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		self.set_slot('title', 'modu ZPT Test Page')
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

class WSGISite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def configure_app(self, application):
		application.base_domain = 'localhost:8888'
		application.base_path = '/modu/examples/zpt'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(RootResource())
