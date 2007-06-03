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
		for key in dir(req):
			output += key + ': ' + str(getattr(req, key)) + "\n"
		return output 

config.base_path = '/dathomir/examples/basic'
config.activate(RootResource())
config.activate(TestResource())
