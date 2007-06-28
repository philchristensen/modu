#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import resource

import cStringIO, unittest

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
