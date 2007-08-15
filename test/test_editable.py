# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import time

from twisted.trial import unittest

from modu import persist
from modu.web import editable, app
from modu.persist import storable, adbapi
from modu.util import form, theme, test, tags

TEST_TABLES = """
DROP TABLE IF EXISTS `page`;
CREATE TABLE IF NOT EXISTS `page` (
  `id` bigint(20) unsigned NOT NULL default 0,
  `category_id` bigint(20) NOT NULL default 0,
  `code` varchar(128) NOT NULL default '',
  `content` text NOT NULL,
  `title` varchar(64) NOT NULL default '',
  `created_date` int(11) NOT NULL default '0',
  `modified_date` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `category`;
CREATE TABLE IF NOT EXISTS `category` (
  `id` bigint(20) unsigned NOT NULL default 0,
  `code` varchar(255) NOT NULL default '',
  `title` varchar(255) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `category` (id, code, title) VALUES
(1, 'drama', 'Drama'), (2, 'sci-fi', 'Science Fiction'),
(3, 'bio', 'Biography'), (4, 'horror', 'Horror');

DROP TABLE IF EXISTS `guid`;
CREATE TABLE IF NOT EXISTS `guid` (
  `guid` bigint(20) unsigned NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `guid` VALUES (5);
"""

class EditableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.Store.get_store()
		if not(self.store):
			pool = adbapi.connect('MySQLdb://modu:modu@localhost/modu')
			self.store = persist.Store(pool)
			#self.store.debug_file = sys.stderr
		
		global TEST_TABLES
		for sql in TEST_TABLES.split(";"):
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
	
	
	def test_checkboxfield(self):
		test_itemdef = editable.itemdef(
			selected		= editable.definition(
								type		= 'CheckboxField',
								label		= 'Selected'
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.selected = 1
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['selected'](type='checkbox', label='Selected', checked=True)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_stringfield(self):
		test_itemdef = editable.itemdef(
			name			= editable.definition(
								type		= 'StringField',
								label		= 'Name'
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name'](type='textfield', label='Name', value='Test Name')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_linked_labelfield(self):
		test_itemdef = editable.itemdef(
			__special		= editable.definition(
								item_url	= 'http://www.example.com'
							),
			linked_name		= editable.definition(
								type		= 'LabelField',
								label		= 'Name',
								link		= True
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.linked_name = 'Linked Name'
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['linked_name'](type='label', label='Name', value='Linked Name',
										prefix=tags.a(href='http://www.example.com', __no_close=True), suffix='</a>')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_selectfield(self):
		options = {'admin':'Administrator', 'user':'User'}
		test_itemdef = editable.itemdef(
			user_type		= editable.definition(
								type		= 'SelectField',
								label		= 'Type',
								options		= options
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.user_type = 'user'
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['user_type'](type='select', label='Type', value='user', options=options)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_foreign_selectfield(self):
		options = {1:'Drama', 2:'Science Fiction', 3:'Biography', 4:'Horror'}
		test_itemdef = editable.itemdef(
			category_id		= editable.definition(
								type		= 'ForeignSelectField',
								label		= 'Category',
								ftable		= 'category',
								fvalue		= 'id',
								flabel		= 'title'
							)
		)
		
		req = self.get_request()
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='select', label='Category', value=3, options=options)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_foreign_labelfield(self):
		test_itemdef = editable.itemdef(
			category_id		= editable.definition(
								type		= 'ForeignLabelField',
								label		= 'Category',
								ftable		= 'category',
								fvalue		= 'code',
								flabel		= 'title'
							)
		)
		
		req = self.get_request()
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 'bio'
		
		itemdef_form = test_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='label', label='Category', value='Biography')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_validation(self):
		self.validation_test_bool = False
		self.prewrite_callback_bool = False
		
		def test_validator(req, form, storable):
			self.validation_test_bool = True
			return True
		
		def test_prewrite(req, form, storable):
			self.prewrite_callback_bool = True
			return True
		
		test_itemdef = editable.itemdef(
			__config		= editable.definition(
								prewrite_callback = test_prewrite
							),
			title			= editable.definition(
								type		= 'StringField',
								label		= 'Title',
								validator	= test_validator
							)
		)
		
		form_data = {'page-form[title]':'Sample Title', 'page-form[save]':'save'}
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
		
		form_data = {'page-form[title]':'', 'page-form[save]':'save'}
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
