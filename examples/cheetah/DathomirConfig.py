# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.app import handler
from dathomir import app, resource

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
		for key in req:
			output += key + ': ' + str(req[key]) + "\n"
		self.add_slot('request_data', output)
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

app.base_url = '/dathomir/examples/cheetah'
app.db_url = None
app.session_class = None
app.initialize_store = False
app.activate(RootResource())
