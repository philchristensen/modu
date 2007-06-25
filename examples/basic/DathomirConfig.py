# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.web.modpython import handler
from dathomir import app, resource

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
		output = "This is the web root at: " + req['dathomir.path'] + "\n"
		for key in req:
			output += key + ': ' + str(req[key]) + "\n"
		from mod_python import apache
		output += '\n\n'
		for name in dir(apache):
			output += name + ': ' + str(getattr(apache, name)) + "\n"
		return output 

app.base_url = '/dathomir/examples/basic'
app.db_url = None
app.session_class = None
app.initialize_store = False
app.activate(RootResource())
app.activate(TestResource())
