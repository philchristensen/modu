from dathomir.config import handler
from dathomir import config, resource

import os

class TestResource(resource.TemplateResource):
	def get_paths(self):
		return ['/test']
	
	def prepare_content(self, request):
		self.add_slot('test', 'This is my test string.')
		self.add_slot('one', 1)
		self.add_slot('two', 2)
	
	def get_template(self, request):
		return 'The string is "$test", one is $one, two is $two'

class RootResource(resource.TemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, request):
		pass
	
	def get_content_type(self, request):
		return 'text/plain'
	
	def get_template(self, request):
		output = "This is the web root at: " + request.dathomir_path + "\n"
		for key in dir(request):
			output += key + ': ' + str(getattr(request, key)) + "\n"
		return output 

config.base_path = '/dathomir/test'
config.activate(RootResource())
config.activate(TestResource())
