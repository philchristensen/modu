# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Tests for the various built-in editable datatypes.

This module is getting big, and may need to be split into smaller pieces.
"""

import time, datetime

from twisted.trial import unittest

from modu import persist
from modu.editable.datatypes import string, relational, boolean, select
from modu.web import app
from modu.editable import define
from modu.persist import storable, dbapi
from modu.util import form, test, tags, queue, date

class DatatypesTestCase(unittest.TestCase):
	"""
	Tests for the various built-in editable datatypes.
	"""
	
	def setUp(self):
		"""
		Initializes the testing tables in the modu test database.
		"""
		pool = dbapi.connect('MySQLdb://modu:modu@localhost/modu')
		self.store = persist.Store(pool)
		#self.store.debug_file = sys.stderr
		
		for sql in test.TEST_TABLES.split(";"):
			if(sql.strip()):
				self.store.pool.runOperation(sql)
	
	
	def get_request(self, form_data={}):
		"""
		The request generator for this TestCase.
		
		This particular implementation will return a Request object
		that has had a store instance defined for it.
		"""
		environ = test.generate_test_wsgi_environment(form_data)
		environ['REQUEST_URI'] = '/app-test/test-resource'
		environ['HTTP_HOST'] = '____store-test-domain____:1234567'
		environ['SERVER_NAME'] = '____store-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		req['modu.pool'] = dbapi.connect(application.db_url)
		req['modu.user'] = test.TestAdminUser()
		queue.activate_content_queue(req)
		persist.activate_store(req)
		
		return req
	
	
	def test_checkbox_field(self):
		"""
		Test for L{modu.editable.datatypes.boolean.CheckboxField}
		"""
		test_itemdef = define.itemdef(
			selected		= boolean.CheckboxField(
								label		= 'Selected',
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		
		test_storable = storable.Storable('test')
		test_storable.selected = 1
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['selected'](type='checkbox', label='Selected', checked=True)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002, attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_checkbox_field_listing(self):
		"""
		Test for L{modu.editable.datatypes.boolean.CheckboxField} as displayed in a generated form.
		"""
		test_itemdef = define.itemdef(
			selected		= boolean.CheckboxField(
								label		= 'Selected',
								listing		= True,
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		
		test_storable = storable.Storable('test')
		test_storable.selected = 1
		
		itemdef_form = test_itemdef.get_listing(req, [test_storable])[0]
		
		reference_form = form.FormNode('test-row')
		reference_form['selected'](type='checkbox', label='Selected', checked=True, disabled=True)
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_linked_labelfield(self):
		"""
		Test for L{modu.editable.datatypes.string.LabelField}.
		
		...and any other datatype that could support a link prefix/suffix
		"""
		test_itemdef = define.itemdef(
			# Normally base_path is set by the admin resource
			__config		= dict(
								base_path = '/admin'
							),
			linked_name		= string.LabelField(
								label		= 'Name',
								link		= True,
								listing		= True,
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		
		test_storable = storable.Storable('test')
		test_storable.linked_name = 'Linked Name'
		
		itemdef_form = test_itemdef.get_listing(req, [test_storable])
		
		reference_form = form.FormNode('test-row')
		reference_form['linked_name'](type='label', label='Name', value='Linked Name',
										prefix=tags.a(href='http://____store-test-domain____:1234567/app-test/detail/test/0', __no_close=True), suffix='</a>')
		
		itemdef_form_html = itemdef_form[0].render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_stringfield(self):
		"""
		Test for L{modu.editable.datatypes.string.StringField}
		"""
		test_itemdef = define.itemdef(
			name			= string.StringField(
								label		= 'Name',
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name'](type='textfield', label='Name', value='Test Name')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002, attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_stringfield_listing(self):
		"""
		Test for L{modu.editable.datatypes.string.StringField} as displayed in a generated form.
		"""
		test_itemdef = define.itemdef(
			name			= string.StringField(
								label		= 'Name',
								listing		= True,
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		
		test_storable = storable.Storable('test')
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_listing(req, [test_storable])[0]
		
		reference_form = form.FormNode('test-row')
		reference_form['name'](type='label', label='Name', value='Test Name')
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_foreign_labelfield(self):
		"""
		Test for L{modu.editable.datatypes.relational.ForeignLabelField}
		"""
		test_itemdef = define.itemdef(
			category_id		= relational.ForeignLabelField(
								label		= 'Category',
								ftable		= 'category',
								fvalue		= 'code',
								flabel		= 'title',
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.set_factory(req.store.get_factory('page'))
		test_storable.title = "My Title"
		test_storable.category_id = 'bio'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='label', label='Category', value='Biography')
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002, attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_select_field(self):
		"""
		Test for L{modu.editable.datatypes.select.SelectField}
		"""
		options = {'admin':'Administrator', 'user':'User'}
		test_itemdef = define.itemdef(
			user_type		= select.SelectField(
								label		= 'Type',
								options		= options,
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		
		test_storable = storable.Storable('test')
		test_storable.user_type = 'user'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		#options = {'admin':'Administrator', 'user':'User'}
		reference_form = form.FormNode('test-form')
		reference_form['user_type'](type='select', label='Type', value='user', options=options)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002, attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_date_field_arrays(self):
		"""
		Test the date field arrays used to build date selects.
		"""
		months, days = date.get_date_arrays()
		hours, minutes = date.get_time_arrays()
		
		self.failUnlessEqual(days[0], 1, 'Found broken first day: %s' % days[0])
		self.failUnlessEqual(days[-1], 31, 'Found broken last day: %s' % days[-1])
		
		self.failUnlessEqual(hours[0], '00', 'Found broken first hour: %s' % hours[0])
		self.failUnlessEqual(hours[-1], '24', 'Found broken last hour: %s' % hours[-1])
		
		self.failUnlessEqual(minutes[0], '00', 'Found broken first minute: %s' % minutes[0])
		self.failUnlessEqual(minutes[-1], '59', 'Found broken last minute: %s' % minutes[-1])
	
	
	def test_date_field(self):
		"""
		Test for L{modu.editable.datatypes.date.DateField}
		"""
		from modu.editable.datatypes import date as date_datatype
		test_itemdef = define.itemdef(
			start_date			= date_datatype.DateField(
				label			= 'start date:',
				save_format		= 'datetime',
				attributes	= dict(basic_element=False),
			)
		)
		
		req = self.get_request([('test-form[start_date][date][month]',8),
								('test-form[start_date][date][day]',25),
								('test-form[start_date][date][year]',2007),
								('test-form[start_date][date][hour]',23),
								('test-form[start_date][date][minute]',40)
								])
		
		test_storable = storable.Storable('test')
		# +---------------------------+
		# | from_unixtime(1190864400) |
		# +---------------------------+
		# | 2007-09-26 23:40:00       | 
		# +---------------------------+
		test_storable.start_date = datetime.datetime.fromtimestamp(1190864400)
		self.failUnlessEqual(test_storable.start_date.year, 2007, 'Test year was calculated incorrectly as %s' % test_storable.start_date.year)
		
		months, days = date.get_date_arrays()
		hours, minutes = date.get_time_arrays()
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['start_date'](type='fieldset', style='brief', label='start date:')
		reference_form['start_date']['null'](type='checkbox', text="no value", weight=-1, suffix=tags.br(), 
			attributes=dict(onChange='enableDateField(this);'))
		reference_form['start_date']['date'](type='fieldset')
		reference_form['start_date']['date']['month'](type='select', weight=0, options=months, value=8)
		reference_form['start_date']['date']['day'](type='select', weight=1, options=days, value=25)
		reference_form['start_date']['date']['year'](type='textfield', weight=2, size=5, value=2007)
		reference_form['start_date']['date']['hour'](type='select', weight=3, options=hours, value=23)
		reference_form['start_date']['date']['minute'](type='select', weight=4, options=minutes, value=40)
		reference_form['start_date'](
			suffix = tags.script(type="text/javascript")["""
				enableDateField($('#form-item-start_date input'));
			"""],
		)
		
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002,
			attributes=dict(onClick="return confirm('Are you sure you want to delete this record?');"))
		
		itemdef_form_html = str(itemdef_form.render(req))
		reference_form_html = str(reference_form.render(req))
		
		for i in range(len(itemdef_form_html)):
			if(reference_form_html[i] != itemdef_form_html[i]):
				self.fail('Expecting %s (%s) but found %s (%s) at position %d' % (
					reference_form_html[i], reference_form_html[i-20:i+20], itemdef_form_html[i], itemdef_form_html[i-20:i+20], i
				))
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
		
		test_storable.start_date = datetime.datetime.now()
		# this just loads the data, since there was
		# no submit button in the test post data
		itemdef_form.execute(req)
		
		test_itemdef['start_date'].update_storable(req, itemdef_form, test_storable)
		self.failUnlessEqual(test_storable.start_date, datetime.datetime.fromtimestamp(1190864400), 'Date was calculated incorrectly as %s' % test_storable.start_date)
	
	
	def test_date_field2(self):
		req = self.get_request()
		
		months, days = date.get_date_arrays()
		hours, minutes = date.get_time_arrays()
		
		simple_element = form.FormNode('test-form')
		simple_element['start_date'](type='fieldset', style='brief', label='start date:')
		simple_element['start_date']['month'](type='select', weight=0, options=months, value=8)
		simple_element['start_date']['day'](type='select', weight=1, options=days, value=25)
		simple_element['start_date']['year'](type='textfield', weight=2, size=5, value=2007)
		simple_element['start_date']['hour'](type='select', weight=3, options=hours, value=23)
		simple_element['start_date']['minute'](type='select', weight=4, options=minutes, value=40)
		
		date_element = form.FormNode('test-form')
		date_element['start_date'](type='datetime', label='start date:', value=datetime.datetime.fromtimestamp(1190864400))
		
		simple_element_html = str(simple_element.render(req))
		date_element_html = str(date_element.render(req))
		
		for i in range(len(date_element_html)):
			if(simple_element_html[i] != date_element_html[i]):
				self.fail('Expecting %s (%s) but found %s (%s) at position %d' % (
					simple_element_html[i], simple_element_html[i-20:i+20], date_element_html[i], date_element_html[i-20:i+20], i
				))
		
		self.failUnlessEqual(date_element_html, simple_element_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (date_element_html, simple_element_html) )
	
	
	def test_foreign_select_field(self):
		"""
		Test for L{modu.editable.datatypes.relational.ForeignSelectField}
		"""
		options = {1:'Drama', 2:'Science Fiction', 3:'Biography', 4:'Horror', 5:'Science', 6:'Historical Fiction', 7:'Self-Help', 8:'Romance', 9:'Business', 10:'Technical', 11:'Engineering', 12:'Lanugage', 13:'Finance', 14:'Young Readers', 15:'Music', 16:'Dance', 17:'Psychology', 18:'Astronomy', 19:'Physics', 20:'Politics'}
		test_itemdef = define.itemdef(
			category_id		= relational.ForeignSelectField(
								label		= 'Category',
								ftable		= 'category',
								fvalue		= 'id',
								flabel		= 'title',
								attributes	= dict(basic_element=False),
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
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		reference_form = form.FormNode('page-form')
		reference_form['category_id'](type='select', label='Category', value=3, options=options)
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002, attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )
	
	
	def test_foreign_autocomplete_field(self):
		"""
		Test for L{modu.editable.datatypes.relational.ForeignAutocompleteField}
		"""
		test_itemdef = define.itemdef(
			name			= relational.ForeignAutocompleteField(
								label		= 'Name',
								fvalue		= 'id',
								flabel		= 'title',
								ftable		= 'category',
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request()
		req.store.ensure_factory('test')
		
		test_storable = storable.Storable('test')
		test_storable.set_factory(req.store.get_factory('test'))
		test_storable.name = 'Test Name'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		
		reference_form = form.FormNode('test-form')
		reference_form['name'](type='fieldset', style='brief', label='Name')
		reference_form['name']['name-autocomplete'](type='textfield', weight=0,
								attributes={'id':'test-form-name-autocomplete'})
		reference_form['name']['ac-support'](type="markup", weight=1, value=tags.script(type='text/javascript')
									['$("#test-form-name-autocomplete").autocomplete("http://____store-test-domain____:1234567/app-test/autocomplete/test/name", {onItemSelect:select_item("test-form-name-ac-callback"), autoFill:1, selectFirst:1, matchSubset:0, selectOnly:1, formatItem:formatItem, extraParams:{t:%d}, minChars:3});' % int(time.time())])
		reference_form['name']['name'](type='hidden', weight=2, value=0,
								attributes={'id':'test-form-name-ac-callback'})
		reference_form['save'](type='submit', value='save', weight=1000)
		reference_form['cancel'](type='submit', value='cancel', weight=1001)
		reference_form['delete'](type='submit', value='delete', weight=1002, attributes={'onClick':"return confirm('Are you sure you want to delete this record?');"})
		
		itemdef_form_html = itemdef_form.render(req)
		reference_form_html = reference_form.render(req)
		
		self.failUnlessEqual(itemdef_form_html, reference_form_html, "Didn't get expected form output, got:\n%s\n  instead of:\n%s" % (itemdef_form_html, reference_form_html) )	
	
	
	def test_password_field(self):
		"""
		Test for L{modu.editable.datatypes.string.PasswordField}
		"""
		post_data = [('page-form[title][entry]', 'Text Before Encryption'),
					 ('page-form[title][verify]','Text Before Encryption'),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title',
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failIfEqual(test_storable.title, "My Title", "Title field wasn't overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		post_data = [('page-form[title][entry]', 'Text Before Encryption'),
					 ('page-form[title][verify]',''),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title'
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		itemdef_form.execute(req)
		
		self.failIf(test_storable.get_id(), 'Storable was saved.')
		self.failUnlessEqual(test_storable.title, "My Title", "Title field was overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		post_data = [('page-form[title][entry]', ''),
					 ('page-form[title][verify]',''),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title'
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was saved.')
		self.failUnlessEqual(test_storable.title, "My Title", "Title field was overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
	
	
	def test_password_field_noverify(self):
		"""
		Test for L{modu.editable.datatypes.string.PasswordField} without verification.
		"""
		post_data = [('page-form[title]', 'Text Before Encryption'),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title',
								verify		= False,
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failIfEqual(test_storable.title, "My Title", "Title field wasn't overwritten by password datatype")
		self.failIfEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
	
	
	def test_password_field_noencrypt(self):
		"""
		Test for L{modu.editable.datatypes.string.PasswordField} without encryption.
		"""
		post_data = [('page-form[title][entry]', 'Text Before Encryption'),
					 ('page-form[title][verify]','Text Before Encryption'),
					 ('page-form[save]','save')]
		test_itemdef = define.itemdef(
			title		= string.PasswordField(
								label		= 'Encrypted Title',
								encrypt		= False,
								attributes	= dict(basic_element=False),
							)
		)
		
		req = self.get_request(post_data)
		req.store.ensure_factory('page')
		
		test_storable = storable.Storable('page')
		test_storable.title = "My Title"
		test_storable.category_id = 3
		test_storable.content = 'Sample content'
		test_storable.code = 'my-title'
		
		itemdef_form = test_itemdef.get_form(req, test_storable)
		itemdef_form.execute(req)
		
		self.failUnless(test_storable.get_id(), 'Storable was not saved.')
		self.failIfEqual(test_storable.title, "My Title", "Title field wasn't overwritten by password datatype")
		self.failUnlessEqual(test_storable.title, "Text Before Encryption", "Title field wasn't encrypted by password datatype")
	


