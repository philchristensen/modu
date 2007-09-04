# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu.util import test
from modu.web import app

class PathTestCase(unittest.TestCase):
	def get_request(self, request_path):
		environ = test.generate_test_wsgi_environment()
		environ['REQUEST_URI'] = request_path
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		return req
	
	def test_with_path(self):
		req = self.get_request('/app-test/test-resource')
		self.failUnlessEqual(req.app.base_path, '/app-test', "Found %s when expecting %s." % (req.app.base_path, '/app-test'))
		
		expecting = '/app-test/one'
		got = req.get_path('one')
		self.failUnlessEqual(expecting, got, "Found %s when expecting %s." % (got, expecting))
		
		expecting = '/app-test/'
		got = req.get_path('/')
		self.failUnlessEqual(expecting, got, "Found %s when expecting %s." % (got, expecting))
		
		expecting = '/app-test'
		got = req.get_path()
		self.failUnlessEqual(expecting, got, "Found %s when expecting %s." % (got, expecting))
	
	def test_without_path(self):
		req = self.get_request('/test-resource')
		self.failUnlessEqual(req.app.base_path, '/', "Found %s when expecting %s." % (req.app.base_path, '/'))
		
		expecting = '/one'
		got = req.get_path('one')
		self.failUnlessEqual(expecting, got, "Found %s when expecting %s." % (got, expecting))
		
		expecting = '/'
		got = req.get_path('/')
		self.failUnlessEqual(expecting, got, "Found %s when expecting %s." % (got, expecting))
		
		expecting = ''
		got = req.get_path()
		self.failUnlessEqual(expecting, got, "Found %s when expecting %s." % (got, expecting))
