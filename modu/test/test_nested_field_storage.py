# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Test NestedField Storage.
"""

from modu.web import app
from modu.util import form, test

from twisted.trial import unittest

encodings = (('multipart', True), ('standard', False))

class NestedFieldStorageTestCase(unittest.TestCase):
	def get_request(self, post_data, multipart):
		environ = test.generate_test_wsgi_environment(post_data, multipart)
		environ['REQUEST_URI'] = '/app-test/test-resource'
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		return app.configure_request(environ, application)
	
	def test_basic(self):
		post_data = [("test[one][two][three]","value 3"), ('test_basic','test_basic')]
		
		for name, style in encodings:
			req = self.get_request(post_data, style)
			fields = form.NestedFieldStorage(req)
			self.assertEqual(fields['test']['one']['two']['three'].value, 'value 3', 'Did not find "value 3" where expected in %s test.' % name)
			self.assertEqual(len(fields.__dict__['list']), 2, 'Found %d fields in  %s test of NestedFieldStorage::list, expected 2.' % (len(fields.__dict__['list']), name))
	
	def test_list(self):
		post_data = [("test[one][two][three]","value 1"), ("test[one][two][three]","value 2"), ("test[one][two][three]","value 3"), ('test_list','test_list')]
		
		for name, style in encodings:
			req = self.get_request(post_data, style)
			fields = form.NestedFieldStorage(req)
			value = fields['test']['one']['two']['three'].value
			self.failUnless(isinstance(value, list), "Didn't get list back from multivalue post.")
			
			expected = ['value 1', 'value 2', 'value 3']
			value.sort()
			self.assertEqual(value, expected, 'Found %s instead of %s where expected in %s test.' % (value, expected, name))
			self.assertEqual(len(fields.__dict__['list']), 2, 'Found %d fields in  %s test of NestedFieldStorage::list, expected 2.' % (len(fields.__dict__['list']), name))
	
	def test_broken(self):
		post_data = [("test[one]","value 1"), ("test[one][two][three]","value 3"), ('test_broken','test_broken')]
		
		for name, style in encodings:
			req = self.get_request(post_data, style)
			
			fields = form.NestedFieldStorage(req)
			self.assertEqual(fields['test']['one'].value, 'value 1', 'Did not find "value 1" where expected in %s test.' % name)
			self.assertEqual(fields['test[one][two][three]'].value, 'value 3', 'Did not find "value 3" where expected in %s test.' % name)
			self.assertEqual(len(fields.__dict__['list']), 3, 'Found %d fields in %s test of NestedFieldStorage::list, expected 3.' % (len(fields.__dict__['list']), name))
	
	def test_normal(self):
		post_data = [('test_normal','test_normal'), ('sample-form[title]','title field data'), ('sample-form[body]','body field data')]
		
		for name, style in encodings:
			req = self.get_request(post_data, style)
			
			fields = form.NestedFieldStorage(req)
			self.assertEqual(fields['sample-form']['title'].value, 'title field data', 'Did not find sample-form[title] data in %s test.' % name)
			self.assertEqual(fields['sample-form']['body'].value, 'body field data', 'Did not find sample-form[body] data in %s test.' % name)
			self.assertEqual(fields['test_normal'].value, 'test_normal', 'Found "%s" expecting "test_normal_multipart" in %s test.' % (fields['test_normal'].value, name))
			self.assertEqual(len(fields.__dict__['list']), 2, 'Found %d fields in NestedFieldStorage::list, expected 3 in %s test.' % (len(fields.__dict__['list']), name))
