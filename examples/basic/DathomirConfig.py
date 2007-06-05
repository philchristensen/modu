from dathomir.config import handler
from dathomir import config, resource

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
		for key in dir(req):
			output += key + ': ' + str(getattr(req, key)) + "\n"
		from mod_python import apache
		output += '\n\n'
		for name in dir(apache):
			output += name + ': ' + str(getattr(apache, name)) + "\n"
		return output 

config.base_path = '/dathomir/examples/basic'
config.db_url = None
config.session_class = None
config.initialize_store = False
config.activate(RootResource())
config.activate(TestResource())
