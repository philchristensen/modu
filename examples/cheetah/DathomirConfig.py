# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.config import handler
from dathomir import config, resource

from mod_python import util

import os

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		self.add_slot('test', 'This is my test string.')
		self.add_slot('sample_array', ['one', 'two', 'three'])
		self.add_slot('sample_hash', {'one':1, 'two':2, 'three':3})
		
		output = ''
		for key in dir(req):
			output += key + ': ' + str(getattr(req, key)) + "\n"
		self.add_slot('request_data', output)
		#self.add_slot('request_data', util.FieldStorage(req))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

config.base_path = '/dathomir/examples/cheetah'
config.db_url = None
config.session_class = None
config.initialize_store = False
config.activate(RootResource())
