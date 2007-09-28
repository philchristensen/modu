# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os, os.path

from twisted.trial import unittest
from twisted.internet import defer

from zope.interface import implements

from modu.util import test
from modu.web import resource, app
from modu import web

class AppTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_load(self):
		environ = test.generate_test_wsgi_environment()		
		application = app.get_application(environ)
		self.failIf(application is not None, "Got an Application object when expecting None.")
		
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		environ['REQUEST_URI'] = '/app-test/test-resource'
		application = app.get_application(environ)
		self.failIf(application is None, "Didn't get an application object.")
	
	def test_resource(self):
		environ = test.generate_test_wsgi_environment()		
		environ['REQUEST_URI'] = '/app-test/test-resource/this/is/a/long/path?query=some+query'
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		self.failUnlessEqual(req['modu.app'], application)
		self.failUnlessEqual(req['PATH_INFO'].find('?'), -1, 'Found query string in PATH_INFO')
		self.failUnlessEqual(req['SCRIPT_FILENAME'], req['modu.approot'], 'Found incorrect approot')
		self.failUnlessEqual(req['PATH_INFO'], req['modu.path'], 'PATH_INFO was different from modu.path')
		self.failUnlessEqual(req['modu.path'], '/test-resource/this/is/a/long/path', 'modu.path was not as expected: %s' % req['modu.path'])
		
		rsrc = req.get_resource()
		self.failIf(rsrc is None, 'Resource retrieval failed.')
		
		response = rsrc.get_response(req)
		expected = ['this/is/a/long/path']
		self.failUnlessEqual(response, expected, "Found %s instead of %s" % (response, expected))
		
		environ['REQUEST_URI'] = '/app-test/test-delegate/this/is/a/long/path'
		application = app.get_application(environ)
		req = app.configure_request(environ, application)
		rsrc = req.get_resource()
		self.failUnless(resource.IResourceDelegate.providedBy(rsrc), 'Resource did not implement IResourceDelegate.')
		
		rsrc = rsrc.get_delegate(req)
		self.failIf(rsrc is None, 'Resource retrieval failed.')
		
		self.failUnlessEqual(rsrc.get_response(req), ['this/is/a/long/path'], "Did not find expected content")

		environ['REQUEST_URI'] = '/app-test/test-access'
		application = app.get_application(environ)
		req = app.configure_request(environ, application)
		rsrc = req.get_resource()
		self.failUnless(resource.IAccessControl.providedBy(rsrc), 'Resource did not implement IAccessControl.')
		
		self.failUnlessRaises(web.HTTPStatus, rsrc.check_access, req)
		try:
			rsrc = rsrc.check_access(req)
		except web.HTTPStatus, http:
			self.failUnlessEqual(http.status, '401 Unauthorized', "Got unexpected status '%s'" % http.status)
	
	def test_handler(self):
		def start_response(status, headers):
			d.callback([status,headers])
		
		environ = test.generate_test_wsgi_environment()
		
		def check200(result):
			status, headers = result
			self.failUnlessEqual(status, '200 OK', "App handler returned unexpected status, '%s'" % status)
		
		def check404(result):
			status, headers = result
			self.failUnlessEqual(status, '404 Not Found', "App handler returned unexpected status, '%s'" % status)
		
		# Shouldn'f find anything because server in environ is
		# still set to 'localhost'
		d = defer.Deferred()
		environ['REQUEST_URI'] = '/app-test/test-resource'
		app.handler(environ, start_response)
		d.addCallback(check404)
		
		# Set up the proper host info
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		environ['REQUEST_URI'] = '/app-test/test-resource/this/is/a/long/path?query=some+query'
		environ['SCRIPT_FILENAME'] = ''
		
		# Test for valid path
		d = defer.Deferred()
		app.handler(environ, start_response)
		d.addCallback(check200)
		
		# Test for invalid path
		d = defer.Deferred()
		environ['REQUEST_URI'] = '/app-test'
		app.handler(environ, start_response)
		d.addCallback(check404)

