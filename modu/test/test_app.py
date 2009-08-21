# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Tests for the L{modu.web.app} module.
"""

import os, os.path

from twisted.trial import unittest
from twisted.internet import defer

from zope.interface import implements

from modu.util import test
from modu.web import resource, app
from modu import web

class AppTestCase(unittest.TestCase):
	"""
	Test the WSGI application flow.
	"""
	def get_request(self, uri, form_data={}, hostname='____basic-test-domain____'):
		"""
		The request generator for this TestCase.
		"""
		environ = test.generate_test_wsgi_environment(form_data)
		
		environ['REQUEST_URI'] = uri
		environ['HTTP_HOST'] = '%s:1234567' % hostname
		environ['SERVER_NAME'] = hostname
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		
		return req
	
	def test_mutate_application(self):
		req = self.get_request('/')
		req.app.make_immutable()
		
		self.failUnlessRaises(AttributeError, setattr, req.app, 'base_path', 'something else')
	
	def test_jit(self):
		req = self.get_request('/')
		
		self.failUnless(req.get('modu.session', None) is None)
		self.failUnless(req.get('modu.user', None) is None)
		self.failUnless(req.get('modu.pool', None) is None)
		self.failUnless(req.get('modu.store', None) is None)
	
	def test_jit_usage(self):
		req = self.get_request('/app-test/test-resource', hostname='____store-test-domain____')
		
		self.failUnless(req.get('modu.store', None) is None)
		self.failIf(req.store is None)
	
	def test_load(self):
		"""
		A functional test for Application instantiation.
		
		This test attempts to load the basic test application defined in
		L{modu.sites.test_site} by creating a sample environ dict, passed
		to L{modu.web.app.get_application()}.
		"""
		environ = test.generate_test_wsgi_environment()
		environ['HTTP_HOST'] = 'not-a-valid-domain.com'
		environ['REQUEST_URI'] = '/'
		
		application = app.get_application(environ)
		self.failIf(application is not None, "Got an Application object when expecting None.")
		
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		environ['REQUEST_URI'] = '/app-test/test-resource'
		application = app.get_application(environ)
		self.failIf(application is None, "Didn't get an application object.")
	
	
	def test_request(self):
		"""
		Test various request variables that are created during app configuration.
		"""
		req = self.get_request('/app-test/test-resource/this/is/a/long/path?query=some+query')
		
		self.failUnlessEqual(req['PATH_INFO'].find('?'), -1, 'Found query string in PATH_INFO')
		self.failUnlessEqual(req['PATH_INFO'], req['modu.path'], 'PATH_INFO was different from modu.path')
		self.failUnlessEqual(req['modu.path'], '/test-resource/this/is/a/long/path', 'modu.path was not as expected: %s' % req['modu.path'])
	
	
	def test_resource_retrieval(self):
		"""
		Test basic access to a resource based on URL.
		"""
		req = self.get_request('/app-test/test-resource/this/is/a/long/path?query=some+query')
		
		rsrc = req.get_resource()
		self.failIf(rsrc is None, 'Resource retrieval failed.')
		
		response = rsrc.get_response(req)
		expected = ['this/is/a/long/path']
		self.failUnlessEqual(response, expected, "Found %s instead of %s" % (response, expected))
	
	
	def test_resource_delegation(self):
		"""
		Test resource delegation by L{modu.web.resource.IResourceDelegate}
		"""
		req = self.get_request('/app-test/test-delegate/this/is/a/long/path')
		
		rsrc = req.get_resource()
		self.failUnless(resource.IResourceDelegate.providedBy(rsrc), 'Resource did not implement IResourceDelegate.')
		
		rsrc = rsrc.get_delegate(req)
		self.failIf(rsrc is None, 'Resource retrieval failed.')
		
		self.failUnlessEqual(rsrc.get_response(req), ['this/is/a/long/path'], "Did not find expected content")
	
	
	def test_resource_access_control(self):
		"""
		Test resource protection by L{modu.web.resource.IAccessControl}
		"""
		req = self.get_request('/app-test/test-access')
		
		rsrc = req.get_resource()
		self.failUnless(resource.IAccessControl.providedBy(rsrc), 'Resource did not implement IAccessControl.')
		
		self.failUnlessRaises(web.HTTPStatus, rsrc.check_access, req)
		try:
			rsrc = rsrc.check_access(req)
		except web.HTTPStatus, http:
			self.failUnlessEqual(http.status, '401 Unauthorized', "Got unexpected status '%s'" % http.status)
	
	
	def test_handler(self):
		"""
		A functional test for the WSGI handler.
		"""
		def start_response(status, headers):
			d.callback([status,headers])
		
		environ = test.generate_test_wsgi_environment()
		
		def check200(result):
			status, headers = result
			self.failUnlessEqual(status, '200 OK', "App handler returned unexpected status, '%s'" % status)
		
		def check404(result):
			status, headers = result
			self.failUnlessEqual(status, '404 Not Found', "App handler returned unexpected status, '%s'" % status)
		
		def check500(result):
			status, headers = result
			self.failUnlessEqual(status, '500 Internal Server Error', "App handler returned unexpected status, '%s'" % status)
		
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
		
		# Test for valid path
		d = defer.Deferred()
		app.handler(environ, start_response)
		d.addCallback(check200)
		
		# Test for invalid path
		d = defer.Deferred()
		environ['REQUEST_URI'] = '/app-test'
		app.handler(environ, start_response)
		d.addCallback(check404)
		
		# Test for exceptions
		d = defer.Deferred()
		environ['REQUEST_URI'] = '/app-test/test-resource/exception'
		app.handler(environ, start_response)
		d.addCallback(check500)

