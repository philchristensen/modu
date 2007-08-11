#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os, os.path

from twisted.trial import unittest

from zope.interface import implements

from modu.util import test
from modu.web import resource, app

class AppTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_load(self):
		environ = test.generate_test_wsgi_environment()		
		application = app.get_application(environ)
		self.failIf(application is not None, "Got an Application object when expecting None.")
		
		environ['HTTP_HOST'] = '____test-domain____:1234567'
		environ['SERVER_NAME'] = '____test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		environ['REQUEST_URI'] = '/app-test'
		application = app.get_application(environ)
		self.failIf(application is None, "Didn't get an application object.")
	
	def test_resource(self):
		environ = test.generate_test_wsgi_environment()		
		environ['REQUEST_URI'] = '/app-test'
		environ['SCRIPT_FILENAME'] = os.getcwd()
		
		from modu.sites import test_site
		site = test_site.BasicTestSite()
		application = app.Application(site)
		
		site.initialize(application)
		application.activate(TestResource())
		
		req = app.configure_request(environ, application)
		
		tree = application.get_tree()
		rsrc = tree.parse(req.path)
		self.failIf(rsrc is None, 'Resource retrieval failed.')
		
		req['modu.tree'] = tree


class TestResource(resource.Resource):
	implements(resource.IContent)
	
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		pass
	
	def get_content_type(self, req):
		pass
	
	def get_content(self, req):
		pass