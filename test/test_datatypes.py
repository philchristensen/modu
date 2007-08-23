# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import time

from twisted.trial import unittest

from modu import persist
from modu.editable.datatypes import string, relational, boolean, select
from modu.web import app
from modu.editable import define
from modu.persist import storable, adbapi
from modu.util import form, test, tags

class DatatypesTestCase(unittest.TestCase):
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
	
	
	def test_checkbox_field(self):
		test_itemdef = define.itemdef(
			selected		= boolean.CheckboxField(
								label		= 'Selected'
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.selected = 1
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['selected'](type='checkbox', label='Selected', checked=True)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_checkbox_field_listing(self):
		test_itemdef = define.itemdef(
			selected		= boolean.CheckboxField(
								label		= 'Selected',
								listing		= True
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.selected = 1
		
		itemdef_form = test_itemdef.get_listing([test_storable])[0]
		
		reference_form = form.FormNode('test-form-0')
		reference_form['selected'](type='checkbox', label='Selected', checked=True, disabled=True)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_linked_labelfield(self):
		test_itemdef = define.itemdef(
			__special		= define.definition(
								item_url	= 'http://www.example.com'
							),
			linked_name		= string.LabelField(
								label		= 'Name',
								link		= True
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.linked_name = 'Linked Name'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['linked_name'](type='label', label='Name', value='Linked Name',
										prefix=tags.a(href='http://www.example.com', __no_close=True), suffix='</a>')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_stringfield(self):
		test_itemdef = define.itemdef(
			name			= string.StringField(
								label		= 'Name'
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name'](type='textfield', label='Name', value='Test Name')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_stringfield_listing(self):
		test_itemdef = define.itemdef(
			name			= string.StringField(
								label		= 'Name',
								listing		= True
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_listing([test_storable])[0]
		
		reference_form = form.FormNode('test-form-0')
		reference_form['name'](type='label', label='Name', value='Test Name')
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_foreign_labelfield(self):
		test_itemdef = define.itemdef(
			category_id		= relational.ForeignLabelField(
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
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='label', label='Category', value='Biography')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_select_field(self):
		options = {'admin':'Administrator', 'user':'User'}
		test_itemdef = define.itemdef(
			user_type		= select.SelectField(
								label		= 'Type',
								options		= options
							)
		)
		
		test_storable = storable.Storable('test')
		test_storable.user_type = 'user'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['user_type'](type='select', label='Type', value='user', options=options)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		req = self.get_request()
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_foreign_select_field(self):
		options = {1:'Drama', 2:'Science Fiction', 3:'Biography', 4:'Horror', 5:'Science', 6:'Historical Fiction', 7:'Self-Help', 8:'Romance', 9:'Business', 10:'Technical', 11:'Engineering', 12:'Lanugage', 13:'Finance', 14:'Young Readers', 15:'Music', 16:'Dance', 17:'Psychology', 18:'Astronomy', 19:'Physics', 20:'Politics'}
		test_itemdef = define.itemdef(
			category_id		= relational.ForeignSelectField(
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
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='select', label='Category', value=3, options=options)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_foreign_autocomplete_field(self):
		test_itemdef = define.itemdef(
			name			= relational.ForeignAutocompleteField(
								label		= 'Name',
								url			= '/autocomplete/url',
								fvalue		= 'id',
								flabel		= 'title',
								ftable		= 'category'
							)
		)
		
		req = self.get_request()
		req.store.ensure_factory('test')
		
		test_storable = storable.Storable('test')
		test_storable.set_factory(req.store.get_factory('test'))
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name-ac-fieldset'](type='fieldset', style='brief', label='Name')
		reference_form['name-ac-fieldset']['name-autocomplete'](type='textfield', weight=0,
								attributes={'id':'test-form-name-autocomplete'})
		reference_form['name-ac-fieldset']['ac-support'](weight=1, value=tags.script(type='text/javascript')
									['$("#test-form-name-autocomplete").autocomplete("/autocomplete/url", {onItemSelect:select_foreign_item("test-form-name-ac-callback"), autoFill:1, selectFirst:1, selectOnly:1, minChars:3, maxItemsToShow:10});'])
		reference_form['name-ac-fieldset']['name'](type='hidden', weight=2, value=0,
								attributes={'id':'test-form-name-ac-callback'})
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1000)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_password_field(self):
		post_data = [('page-form[title-entry]', 'Text Before Encryption'),
					 ('page-form[title-verify]','Text Before Encryption'),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title'
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failIfEqual(test_storable.title, "My Title", "Title field wasn't overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		post_data = [('page-form[title-entry]', 'Text Before Encryption'),
					 ('page-form[title-verify]',''),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title'
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		itemdef_form = test_itemdef.get_form(test_storable)
		itemdef_form.execute(req)
		
		self.failIf(test_storable.get_id(), 'Storable was saved.')
		self.failUnlessEqual(test_storable.title, "My Title", "Title field was overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		post_data = [('page-form[title-entry]', ''),
					 ('page-form[title-verify]',''),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title'
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		itemdef_form = test_itemdef.get_form(test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was saved.')
		self.failUnlessEqual(test_storable.title, "My Title", "Title field was overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
	
	
	def test_password_field_noverify(self):
		post_data = [('page-form[title]', 'Text Before Encryption'),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title',
								verify		= False
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failIfEqual(test_storable.title, "My Title", "Title field wasn't overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
	
	
	def test_password_field_noencrypt(self):
		post_data = [('page-form[title-entry]', 'Text Before Encryption'),
					 ('page-form[title-verify]','Text Before Encryption'),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title',
								encrypt		= False
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form(test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failIfEqual(test_storable.title, "My Title", "Title field wasn't overwritten by password datatype")
		self.failUnlessEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
	


