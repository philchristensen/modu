# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web.modpython import handler
from modu.web import app, resource

from mod_python import util

import os

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		self.set_slot('test', 'This is my test string.')
		self.set_slot('sample_array', ['one', 'two', 'three'])
		self.set_slot('sample_hash', {'one':1, 'two':2, 'three':3})
		
		output = ''
		for key in req:
			output += key + ': ' + str(req[key]) + "\n"
		self.set_slot('request_data', req['wsgi.input'].read())
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

app.base_path = '/modu/examples/cheetah'
app.db_url = None
app.session_class = None
app.initialize_store = False
app.activate(RootResource())
