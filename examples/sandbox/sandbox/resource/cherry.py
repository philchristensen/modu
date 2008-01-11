# Modu Sandbox
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import resource

class Resource(resource.CherryTemplateResource):
	def get_paths(self):
		return ['/cherry']
	
	def prepare_content(self, req):
		self.set_slot('test', 'This is my test string.')
		self.set_slot('sample_array', ['one', 'two', 'three'])
		self.set_slot('sample_hash', {'one':1, 'two':2, 'three':3})
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'cherry.html.tmpl' 
