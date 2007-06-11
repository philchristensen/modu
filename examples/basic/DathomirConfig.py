# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.app import handler, accesshandler
from dathomir import app, resource

import os

class TestResource(resource.TemplateResource):
	def get_paths(self):
		return ['/test']
	
	def prepare_content(self, req):
		self.add_slot('test', 'This is my test string.')
		self.add_slot('one', 1)
		self.add_slot('two', 2)
	
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
		output = "This is the web root at: " + req.dathomir_path + "\n"
		output += "meets_conditions() returns: " + str(req.meets_conditions()) + "\n"
		output += 'access output: ' + req.debug_output + "\n\n"
		for key in dir(req):
			output += key + ': ' + str(getattr(req, key)) + "\n"
		from mod_python import apache
		output += '\n\n'
		for name in dir(apache):
			output += name + ': ' + str(getattr(apache, name)) + "\n"
		return output 

app.base_path = '/dathomir/examples/basic'
app.db_url = None
app.session_class = None
app.initialize_store = False
app.activate(RootResource())
app.activate(TestResource())
