# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Tests the L{modu.util.form.FormNode} framework.
"""

import copy

from modu.util import form, test
from modu.web import app

from twisted.trial import unittest

class FormTestCase(unittest.TestCase):
	"""
	Test the non-theme-related aspects of form use.
	"""
	def get_request(self, post_data={}, multipart=True):
		"""
		The request generator for this TestCase.
		
		This generator can also create multipart post data.
		"""
		environ = test.generate_test_wsgi_environment(post_data, multipart)
		environ['REQUEST_URI'] = '/app-test/test-resource'
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		
		return req
	
	
	def test_basic_form(self):
		"""
		Test the basic syntax and field features of forms.
		"""
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['title'](type='textfield', title='Title', required=True, description='This is the title field')
		self.failUnlessEqual(frm['title'].attributes['type'], 'textfield', "Didn't find correct type.")
		self.failUnlessEqual(frm['title'].attributes['title'], 'Title', "Didn't find correct title.")
		self.failUnlessEqual(frm.attributes['enctype'], 'multipart/form-data', "Didn't find correct enctype.")
	
	
	def test_element_path(self):
		"""
		Test the path function for fieldsets.
		"""
		frm = form.FormNode('test-form')
		frm['one']['two']['three']['four'](type='text')
		result = '/'.join(frm['one']['two']['three']['four'].get_element_path())
		expecting = 'test-form/one/two/three/four'
		self.failUnlessEqual(result, expecting, "Element path was incorrect, got '%s' when expecting '%s'" % (result, expecting))
	
	
	def test_fieldset(self):
		"""
		Test fieldsets.
		"""
		frm = form.FormNode('test-form')
		frm['title-area'](type='fieldset', collapsed=False, collapsible=True, title='Title Area')
		frm['title-area']['title'](type='textfield', title='Title', required=True, description='This is the title field')
		
		self.failUnlessEqual(frm['title-area'].attributes['type'], 'fieldset', "Didn't find correct type.")
		self.failUnlessEqual(frm['title-area'].children['title'], frm['title-area']['title'], "Didn't find nested child.")
	
	
	def test_validation(self):
		"""
		Test the validation flow.
		"""
		form_data = [('test-form[title]','Sample Title'), ('test-form[submit]','submit')]
		req = self.get_request(form_data)
		
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['title'](type='textfield', title='Title', required=True, description='This is the title field')
		frm['submit'](type='submit')
		
		def _submit(req, form):
			raise RuntimeError('submit')
		
		def _validate_fail(req, form):
			return False
		
		def _validate_pass(req, form):
			return True
		
		frm.validate = _validate_fail
		frm.submit = _submit
		
		try:
			frm.execute(req)
		except RuntimeError, e:
			self.fail('Submit handle was fired inappropriately.')
		
		frm.validate = _validate_pass
		
		self.failUnlessRaises(RuntimeError, frm.execute, req)
		

