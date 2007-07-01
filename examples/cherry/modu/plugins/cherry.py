# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web.modpython import handler
from modu.web import app, resource

from modu.web.app import ISite
from zope.interface import classProvides
from twisted import plugin

import os

class RootResource(resource.CherryTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		self.set_slot('test', 'This is my test string.')
		self.set_slot('sample_array', ['one', 'two', 'three'])
		self.set_slot('sample_hash', {'one':1, 'two':2, 'three':3})
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

class CherrySite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def configure_app(self, application):
		application.base_domain = 'localhost:8888'
		application.base_path = '/modu/examples/cherry'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(RootResource())
