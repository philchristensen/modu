#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

import unittest, socket

from modu.web import resource

class TestResource(resource.CheetahTemplateResource):
	def __init__(self, test_case_class):
		super(TestResource, self).__init__()
		self.test_case_class = test_case_class
	
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		stream = cStringIO.StringIO()
		runner = unittest.TextTestRunner(stream=stream, descriptions=1, verbosity=1)
		loader = unittest.TestLoader()
		
		self.test_case_class.req = req
		test = loader.loadTestsFromTestCase(self.test_case_class)
		runner.run(test)
		
		self.set_slot('content', stream.getvalue())
		
		stream.close()
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

def generate_test_wsgi_environment(post={}):
	"""
	Set REQUEST_URI
	Set SCRIPT_NAME to app.base_path
	Set SCRIPT_FILENAME to intended approot
	"""
	environ = {}
	environ['wsgi.errors'] = StringIO.StringIO()
	environ['wsgi.file_wrapper'] = file

	input_data = StringIO.StringIO()
	if(post):
		for name,value in post.iteritems():
			input_data.write("------TestingFormBoundaryJe0Hll5QdEhCQiZj\n")
			input_data.write("Content-Disposition: form-data; name=\"%s\"\n\n" % name)
			input_data.write("%s\n" % value)
		input_data.write("------TestingFormBoundaryJe0Hll5QdEhCQiZj--\n")
	environ['wsgi.input'] = input_data
	
	environ['GATEWAY_INTERFACE'] = 'CGI/1.1'
	environ['HTTPS'] = 'off'
	environ['HTTP_ACCEPT'] = 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5'
	environ['HTTP_ACCEPT_ENCODING'] = 'gzip, deflate'
	environ['HTTP_ACCEPT_LANGUAGE'] = 'en'
	environ['HTTP_CONNECTION'] = 'keep-alive'
	environ['HTTP_HOST'] = 'localhost:8888'
	environ['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/522.11.1 (KHTML, like Gecko) Version/3.0.3 Safari/522.12.1'
	environ['QUERY_STRING'] = ''
	environ['REMOTE_ADDR'] = '127.0.0.1'
	environ['REMOTE_HOST'] = socket.gethostname()
	environ['REMOTE_PORT'] = '56546'
	environ['REQUEST_METHOD'] = 'GET'
	environ['REQUEST_SCHEME'] = 'http'
	environ['SCRIPT_NAME'] = ''
	environ['SERVER_NAME'] = 'localhost'
	environ['SERVER_PORT'] = '8888'
	environ['SERVER_PORT_SECURE'] = '0'
	environ['SERVER_PROTOCOL'] = 'HTTP/1.1'
	environ['SERVER_SOFTWARE'] = 'TwistedWeb/2.5.0+rUnknown'
	environ['wsgi.multiprocess'] = 'False'
	environ['wsgi.multithread'] = 'True'
	environ['wsgi.run_once'] = 'False'
	environ['wsgi.url_scheme'] = 'http'
	environ['wsgi.version'] = '(1, 0)'
	
	return environ
