# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
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
	
	
	def test_attr(self):
		"""
		Make sure the different attribute accessor modes work.
		"""
		frm = form.FormNode('test-form')
		frm['one'](
			some_attrib = True,
		)
		frm['one']['two']['three']['four'](type='text')
		self.failUnlessEqual(frm['one']['two']['three']['four'].attr('some_attrib', False, recurse=True), True)
		self.failUnlessEqual(frm['one'].attr('some_attrib', False), True)
		self.failUnlessEqual(frm['one']['two'].attr('some_attrib', False), False)
	
	
	def test_fieldset(self):
		"""
		Test fieldsets.
		"""
		frm = form.FormNode('test-form')
		frm['title-area'](type='fieldset', collapsed=False, collapsible=True, title='Title Area')
		frm['title-area']['title'](type='textfield', title='Title', required=True, description='This is the title field')
		
		self.failUnlessEqual(frm['title-area'].attributes['type'], 'fieldset', "Didn't find correct type.")
		self.failUnlessEqual(frm['title-area']['title'], frm['title-area']['title'], "Didn't find nested child.")
	
	
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
	
	def test_errors(self):
		"""
		Test form errors.
		"""
		form_data = [('test-form[title]','Sample Title'), ('test-form[submit]','submit')]
		req = self.get_request(form_data)
		
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['title'](type='textfield', title='Title', required=True, description='This is the title field')
		frm['submit'](type='submit')
		
		def _validate_error(req, form):
			form.set_error('title', "test error")
			form['title'].set_error("test error 2")
			self.failIf('test error' not in form.get_errors()['title'])
			self.failIf('test error 2' not in form['title'].get_errors())
			return False
		
		frm.validate = _validate_error
		
		if(frm.execute(req)):
			self.fail("Form validation did not fail.")
	
	def test_nested_errors(self):
		"""
		Test nested form errors.
		"""
		form_data = [('test-form[group][title]','Sample Title'), ('test-form[group][submit]','submit')]
		req = self.get_request(form_data)
		
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['group']['title'](type='textfield', title='Title', required=True, description='This is the title field')
		frm['group']['submit'](type='submit')
		
		def _validate_error(req, form):
			form.set_error(['group', 'title'], "test error")
			form['group']['title'].set_error("test error 2")
			self.failIf('test error' not in form.get_errors()['group']['title'])
			self.failIf('test error 2' not in form['group']['title'].get_errors())
			self.failIf('test error' not in form['group'].get_errors()['title'])
			self.failIf('test error 2' not in form['group'].get_errors()['title'])
			return False
		
		frm.validate = _validate_error
		
		if(frm.execute(req)):
			self.fail("Form validation did not fail.")
	
	def test_required_element(self):
		"""
		Test required fields.
		"""
		form_data = [('test-form[title]',''), ('test-form[submit]','submit')]
		req = self.get_request(form_data)
		
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['title'](type='textfield', title='Title', required=True, description='This is the title field')
		frm['submit'](type='submit')
		
		frm.execute(req)
		
		self.failUnless(frm.has_errors())
		
		errs = frm.get_errors()
		self.failUnlessEqual(errs['title'][0], 'You must enter a value for this field.')

