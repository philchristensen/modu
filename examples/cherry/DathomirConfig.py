from dathomir.config import handler
from dathomir import config, resource

import os

class RootResource(resource.CherryTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, request):
		self.add_slot('test', 'This is my test string.')
		self.add_slot('sample_array', ['one', 'two', 'three'])
		self.add_slot('sample_hash', {'one':1, 'two':2, 'three':3})
	
	def get_content_type(self, request):
		return 'text/html'
	
	def get_template(self, request):
		return 'page.html.tmpl' 

config.base_path = '/dathomir/examples/cherry'
config.activate(RootResource())
