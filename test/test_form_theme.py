# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import form, theme

from twisted.trial import unittest
import sys

EXPECTED_TITLE = '<input name="node-form[title]" size="30" type="text" value="" />'
EXPECTED_BODY = '<textarea cols="30" name="node-form[body]" rows="10"></textarea>'
EXPECTED_SUBMIT = '<input name="node-form[submit]" type="submit" value="submit" />'

EXPECTED_CATEGORY = '<select name="node-form[category]">'
EXPECTED_CATEGORY += '<option selected="selected" value="bio">Biography</option>'
EXPECTED_CATEGORY += '<option value="drama">Drama</option>'
EXPECTED_CATEGORY += '<option value="horror">Horror</option>'
EXPECTED_CATEGORY += '<option value="sci-fi">Science Fiction</option>'
EXPECTED_CATEGORY += '</select>'

EXPECTED_LABEL = '<label>%s</label>'
EXPECTED_HELP = '<div class="form-help">%s</div>'
EXPECTED_ELEMENT = '<div class="form-item" id="form-item-%s">%s</div>';

class FormThemeTestCase(unittest.TestCase):
	def setUp(self):
		self.form = form.FormNode('node-form')
		self.form(enctype='multipart/form-data')
		self.form['title'](type='textfield',
					 label='Title',
					 weight=-20,
					 size=30,
					 help='Enter the title of this entry here.'
					)
		self.form['body'](type='textarea',
					label='Body',
					weight=0,
					cols=30,
					rows=10,
					help='Enter the body text as HTML.'
					)
		self.form['category'](type='select',
					label='Category',
					options={'drama':'Drama', 'sci-fi':'Science Fiction', 'bio':'Biography', 'horror':'Horror'},
					value='bio',
					weight=0,
					cols=30,
					rows=10,
					help='Select the category.'
					)
		self.form['submit'](type='submit',
					value='submit',
					weight=100,
					)
		
		self.theme = theme.Theme({})
	
	def tearDown(self):
		pass
	
	def test_title(self):
		title = self.form['title']
		
		title_result = self.theme.form_textfield('node-form', title)
		self.failUnlessEqual(title_result, EXPECTED_TITLE, 'Basic "title" field misrendered as \n`%s`, not \n`%s`' % (title_result, EXPECTED_TITLE));
		
	def test_prefix_suffix(self):
		title = self.form['title']
		title(prefix='##PREFIX##', suffix='##SUFFIX##')
		
		titlefield_result = self.theme.form_element('node-form', title)
		titlefield_check = EXPECTED_ELEMENT % ('title', (EXPECTED_LABEL % title.label) + ('##PREFIX##%s##SUFFIX##' % EXPECTED_TITLE) + (EXPECTED_HELP % title.help))
		self.failUnlessEqual(titlefield_result, titlefield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (titlefield_result, titlefield_check));
		
	def test_title_field(self):
		title = self.form['title']
		
		titlefield_result = self.theme.form_element('node-form', title)
		titlefield_check = EXPECTED_ELEMENT % ('title', (EXPECTED_LABEL % title.label) + EXPECTED_TITLE + (EXPECTED_HELP % title.help))
		self.failUnlessEqual(titlefield_result, titlefield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (titlefield_result, titlefield_check));

	def test_category(self):
		category = self.form['category']
		
		category_result = self.theme.form_select('node-form', category)
		self.failUnlessEqual(category_result, EXPECTED_CATEGORY, 'Basic "category" field misrendered as \n`%s`, not \n`%s`' % (category_result, EXPECTED_CATEGORY));
		
	def test_body(self):
		body = self.form['body']
		
		body_result = self.theme.form_textarea('node-form', body)
		self.failUnlessEqual(body_result, EXPECTED_BODY, 'Basic "body" field misrendered as \n`%s`, not \n`%s`' % (body_result, EXPECTED_BODY));
		
	def test_body_field(self):
		body = self.form['body']
		
		bodyfield_result = self.theme.form_element('node-form', body)
		bodyfield_check = EXPECTED_ELEMENT % ('body', (EXPECTED_LABEL % body.label) + EXPECTED_BODY + (EXPECTED_HELP % body.help))
		self.failUnlessEqual(bodyfield_result, bodyfield_check, '"body" form field misrendered as \n`%s`, not \n`%s`' % (bodyfield_result, bodyfield_check));
	
	def test_submit(self):
		submit = self.form['submit']
		
		submit_result = self.theme.form_submit('node-form', submit)
		self.failUnlessEqual(submit_result, EXPECTED_SUBMIT, 'Basic "submit" field misrendered as \n`%s`, not \n`%s`' % (submit_result, EXPECTED_SUBMIT));
		
	def test_submit_field(self):
		submit = self.form['submit']
		
		submitfield_result = self.theme.form_element('node-form', submit)
		submitfield_check = EXPECTED_ELEMENT % ('submit', EXPECTED_SUBMIT)
		self.failUnlessEqual(submitfield_result, submitfield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (submitfield_result, submitfield_check));

