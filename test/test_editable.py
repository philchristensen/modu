# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import time

from twisted.trial import unittest

from modu import persist
from modu.web import app
from modu.editable import define
from modu.datatypes import string
from modu.persist import storable, adbapi
from modu.util import form, test

class EditableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.Store.get_store()
		if not(self.store):
			pool = adbapi.connect('MySQLdb://modu:modu@localhost/modu')
			self.store = persist.Store(pool)
			#self.store.debug_file = sys.stderr
		
		for sql in test.TEST_TABLES.split(";"):
			if(sql.strip()):
				self.store.pool.runOperation(sql)
	
	
	def tearDown(self):
		pass
	
	
	def get_request(self, form_data={}):
		environ = test.generate_test_wsgi_environment(form_data)
		environ['REQUEST_URI'] = '/app-test/test-resource'
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____store-test-domain____:1234567'
		environ['SERVER_NAME'] = '____store-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		req['modu.pool'] = app.acquire_db(application.db_url)
		persist.activate_store(req)
		
		return req
	
	
	def test_validation(self):
		self.validation_test_bool = False
		self.prewrite_callback_bool = False
		
		def test_validator(req, form, storable):
			self.validation_test_bool = True
			return True
		
		def test_prewrite(req, form, storable):
			self.prewrite_callback_bool = True
			return True
		
		test_itemdef = define.itemdef(
			__config		= define.definition(
								prewrite_callback = test_prewrite
							),
			title			= string.StringField(
								label		= 'Title',
								validator	= test_validator
							)
		)
		
		form_data = [('page-form[title]','Sample Title'), ('page-form[save]','save')]
		req = self.get_request(form_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.code = 'my-title'
		test_storable.category_id = 3
		test_storable.content = 'My Content'
		test_storable.modified_date = int(time.time())
		test_storable.created_date = int(time.time())
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(self.validation_test_bool, "Validation function didn't run")
		self.failUnless(self.prewrite_callback_bool, "Pre-write callback function didn't run")
		
		def test_failed_prewrite(req, form, storable):
			return False
		
		test_itemdef.config['prewrite_callback'] = test_failed_prewrite
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		try:
			itemdef_form.execute(req)
		except RuntimeError, e:
			self.fail("Submit callback ran despite pre-write failure")
		
		def form_validate(req, form):
			return bool(form['title'].attributes['value'])
		
		def form_submit(req, form):
			raise RuntimeError('submit')
		
		form_data = [('page-form[title]',''), ('page-form[save]','save')]
		req = self.get_request(form_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 'bio'
		
		del test_itemdef['title']['validator']
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		itemdef_form['title'].validate = form_validate
		itemdef_form.submit = form_validate
		self.validation_test_bool = False
		self.prewrite_callback_bool = False
		
		try:
			itemdef_form.execute(req)
		except RuntimeError, e:
			self.fail("Submit callback ran despite validation failure")
		
		self.failIf(self.validation_test_bool, "Deleted validator function ran")
		self.failIf(self.prewrite_callback_bool, "Pre-write callback function run despite failing validation")
	
	
	def test_submit(self):
		def postwrite_callback(req, form, storable):
			raise RuntimeError('postwrite')
		
		test_itemdef = define.itemdef(
			__config		= define.definition(
								postwrite_callback = postwrite_callback
			),
			title			= string.StringField(
								label		= 'Title'
			),
			bogus			= string.StringField(
								label		= 'Title',
								implicit_save	= False
			)
		)
		
		form_data = [('page-form[title]','Sample Title'), ('page-form[save]','save')]
		req = self.get_request(form_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.code = 'my-title'
		test_storable.category_id = 3
		test_storable.content = 'My Content'
		test_storable.modified_date = int(time.time())
		test_storable.created_date = int(time.time())
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		self.failUnlessRaises(RuntimeError, itemdef_form.execute, req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failUnlessEqual(test_storable.title, 'Sample Title', 'Storable field `title` was not saved.')
	
