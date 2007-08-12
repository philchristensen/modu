# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu.web import editable, app
from modu.persist import storable
from modu.util import form, theme, test

class EditableTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def get_request(self):
		environ = test.generate_test_wsgi_environment()
		environ['REQUEST_URI'] = '/app-test/test-resource'
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		
		return req
	
	def test_basic(self):
		test_string_itemdef = editable.itemdef(
			name			= editable.definition(
								type		= 'StringField',
								title		= 'Name'
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_string_itemdef.get_detail_form(test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name'](type='textfield', title='Name', value='Test Name')
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )