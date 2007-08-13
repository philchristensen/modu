# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

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
	
	def get_request(self):
		environ = test.generate_test_wsgi_environment()
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
	
	def test_basic(self):
		test_string_itemdef = editable.itemdef(
			name			= editable.definition(
								type		= 'StringField',
								label		= 'Name'
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_string_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name'](type='textfield', label='Name', value='Test Name')
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	def test_link(self):
		test_string_itemdef = editable.itemdef(
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
		
		itemdef_form = test_string_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['linked_name'](type='label', label='Name', value='Linked Name',
										prefix=tags.a(href='http://www.example.com', __no_close=True), suffix='</a>')
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	def test_select(self):
		options = {'admin':'Administrator', 'user':'User'}
		test_string_itemdef = editable.itemdef(
			user_type		= editable.definition(
								type		= 'SelectField',
								label		= 'Type',
								options		= options
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.user_type = 'user'
		
		itemdef_form = test_string_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['user_type'](type='select', label='Type', value='user', options=options)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_foreign_select(self):
		options = {'drama':'Drama', 'sci-fi':'Science Fiction', 'bio':'Biography', 'horror':'Horror'}
		test_string_itemdef = editable.itemdef(
			category_id		= editable.definition(
								type		= 'ForeignSelectField',
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
		
		itemdef_form = test_string_itemdef.get_form('detail', test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='select', label='Category', value='bio', options=options)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )

