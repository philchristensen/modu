# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import resource
from modu.web.app import ISite

from zope.interface import classProvides
from twisted import plugin

import os

class TestResource(resource.TemplateResource):
	def get_paths(self):
		return ['/test']
	
	def prepare_content(self, req):
		self.set_slot('test', 'This is my test string.')
		self.set_slot('one', 1)
		self.set_slot('two', 2)
	
	def get_template(self, req):
		return 'The string is "$test", one is $one, two is $two'

class RootResource(resource.TemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		pass
	
	def get_content_type(self, req):
		return 'text/plain'
	
	def get_template(self, req):
		output = "This is the web root at: " + req['modu.path'] + "\n"
		
		for key in dir(req['modpython.request']):
			item = getattr(req['modpython.request'], key)
			output += key + ': ' + str(item) + "\n"
		
		output += '\n\n'
		
		for key in req:
			output += key + ': ' + str(req[key]) + "\n"
		
		from mod_python import apache
		output += '\n\n'
		for name in dir(apache):
			output += name + ': ' + str(getattr(apache, name)) + "\n"
		
		return output 

class BasicSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def configure_app(self, application):
		application.base_domain = 'localhost:8888'
		application.base_path = '/modu/examples/basic'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(RootResource())
		application.activate(TestResource())
