# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Tests of the form-related functions in L{modu.util.theme}.
"""

from modu.util import form, theme

from twisted.trial import unittest
import sys

EXPECTED_TITLE = '<input name="node-form[title]" size="30" type="text" value="" />'
EXPECTED_BODY = '<textarea cols="30" name="node-form[body]" rows="10"></textarea>'
EXPECTED_SUBMIT = '<input name="node-form[submit]" type="submit" value="submit" />'
EXPECTED_CHECKBOX = '<label><input name="node-form[checkbox]" type="checkbox" value="1" />Checkbox</label>'
EXPECTED_SELECTED_CHECKBOX = '<label><input name="node-form[checkbox]" type="checkbox" value="1" checked />Selected Checkbox</label>'

EXPECTED_CATEGORY = '<select name="node-form[category]">'
EXPECTED_CATEGORY += '<option value="">Select...</option>'
EXPECTED_CATEGORY += '<option value="bio" selected>Biography</option>'
EXPECTED_CATEGORY += '<option value="drama">Drama</option>'
EXPECTED_CATEGORY += '<option value="horror">Horror</option>'
EXPECTED_CATEGORY += '<option value="sci-fi">Science Fiction</option>'
EXPECTED_CATEGORY += '</select>'

EXPECTED_MULTIPLE_CATEGORY = '<select name="node-form[other_category]" size="5" multiple>'
EXPECTED_MULTIPLE_CATEGORY += '<option value="bio" selected>Biography</option>'
EXPECTED_MULTIPLE_CATEGORY += '<option value="drama" selected>Drama</option>'
EXPECTED_MULTIPLE_CATEGORY += '<option value="horror">Horror</option>'
EXPECTED_MULTIPLE_CATEGORY += '<option value="sci-fi" selected>Science Fiction</option>'
EXPECTED_MULTIPLE_CATEGORY += '</select>'

EXPECTED_RADIO = '<label><input name="test-form[radio]" type="radio" value="%s" %s/> %s</label>'

EXPECTED_LABEL = '<label class="field-label">%s</label>'
EXPECTED_HELP = '<div class="form-help">%s</div>'
EXPECTED_ELEMENT = '<div class="form-item" id="form-item-%s">%s</div>';
EXPECTED_ERROR_ELEMENT = '<div class="form-item form-error" id="form-item-%s">%s</div>';

class FormThemeTestCase(unittest.TestCase):
	"""
	Test the HTML output from form theme functions.
	"""
	def setUp(self):
		"""
		Build a sample form with the default theme.
		
		@see: L{modu.util.form.FormNode}
		"""
		self.form = form.FormNode('node-form')
		self.form(enctype='multipart/form-data')
		self.form['title'](type='textfield',
					 label='Title',
					 weight=-20,
					 size=30,
					 help='Enter the title of this entry here.'
					)
		self.form['some_label'](type='label',
					value='this is a label',
					weight=100
					)
		self.form['checkbox'](type='checkbox')
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
					help='Select the category.'
					)
		self.form['other_category'](type='select',
					label='Other Category',
					options={'drama':'Drama', 'sci-fi':'Science Fiction', 'bio':'Biography', 'horror':'Horror'},
					value=['bio', 'drama', 'sci-fi'],
					weight=0,
					help='Select the other categories.',
					multiple=True
					)
		self.form['advanced'](label='Advanced', style='full')
		self.form['advanced']['text1'](type='textfield',
					label='Text 1',
					weight=1,
					size=30,
					help='This is the text1 field.'
					)
		self.form['advanced']['text2'](type='textfield',
					label='Text 2',
					weight=2,
					size=30,
					help='This is the text2 field.'
					)
		self.form['options'](label='Options', style='brief')
		self.form['options']['text3'](type='textfield',
					label='Text 3',
					weight=1,
					size=30,
					help='This is the text3 field.',
					)
		self.form['options']['text4'](type='textfield',
					label='Text 4',
					weight=2,
					size=30,
					help='This is the text4 field.'
					)
		
		self.form['submit'](type='submit',
					value='submit',
					weight=100,
					)
		
		self.theme = theme.Theme({})
	
	def test_radiogroup(self):
		"""
		Test radiogroup rendering.
		"""
		radio_options = {'some-value':'some-label', 'some-other-value':'some-other-label'}
		
		frm = form.FormNode('test-form')
		frm['radio'](
			options = radio_options,
			value = 'some-value'
		)
		
		expected = ''
		keys = radio_options.keys()
		keys.sort()
		
		for key in keys:
			if(key == 'some-value'):
				expected += EXPECTED_RADIO % (key, 'checked ', radio_options[key])
			else:
				expected += EXPECTED_RADIO % (key, '', radio_options[key])
		
		result = self.theme.form_radiogroup('test-form', frm['radio'])
		
		self.failUnlessEqual(result, expected, "Radiogroup rendered as \n%s\n instead of \n%s" % (result, expected))
	
	def test_fieldset(self):
		"""
		Test fieldset rendering.
		"""
		fieldset = self.form['advanced']
		fieldset_result = self.theme.form_element('node-form', fieldset)
		
		content = ''
		for field_name in fieldset:
			field = fieldset[field_name]
			string_field = '<input name="%s" size="30" type="text" value="" />' % field.get_element_name()
			content += EXPECTED_ELEMENT % (field_name, (EXPECTED_LABEL % field.label) + string_field + (EXPECTED_HELP % field.help))
		
		expected_result = EXPECTED_ELEMENT % (fieldset.name, (EXPECTED_LABEL % 'Advanced') + content)
		self.failUnlessEqual(fieldset_result, expected_result, 'Fieldset "advanced" misrendered as \n`%s`, not \n`%s`' % (fieldset_result, expected_result));
	
	def test_fieldset_brief(self):
		"""
		Test brief fieldset rendering.
		"""
		fieldset = self.form['options']
		fieldset_result = self.theme.form_element('node-form', fieldset)
		
		content = ''
		for field_name in fieldset:
			field = fieldset[field_name]
			content += '<input name="%s" size="30" type="text" value="" />' % field.get_element_name()
		
		expected_result = EXPECTED_ELEMENT % (fieldset.name, (EXPECTED_LABEL % 'Options') + content)
		self.failUnlessEqual(fieldset_result, expected_result, 'Fieldset "options" misrendered as \n`%s`, not \n`%s`' % (fieldset_result, expected_result));
	
	def test_label(self):
		"""
		Test label rendering.
		"""
		some_label = self.form['some_label']
		
		some_label_result = self.theme.form_label('node-form', some_label)
		expected_result = '<label>this is a label</label>'
		self.failUnlessEqual(some_label_result, expected_result, 'Basic "some_label" field misrendered as \n`%s`, not \n`%s`' % (some_label_result, expected_result));
		
	def test_checkbox(self):
		"""
		Test checkbox rendering.
		"""
		checkbox = self.form['checkbox'](text='Checkbox')
		
		checkbox_result = self.theme.form_checkbox('node-form', checkbox)
		self.failUnlessEqual(checkbox_result, EXPECTED_CHECKBOX, 'Basic "checkbox" field misrendered as \n`%s`, not \n`%s`' % (checkbox_result, EXPECTED_CHECKBOX));
		
	def test_selected_checkbox(self):
		"""
		Test selected checkbox rendering.
		"""
		checkbox = self.form['checkbox'](text='Selected Checkbox')
		checkbox(checked=True)
		
		checkbox_result = self.theme.form_checkbox('node-form', checkbox)
		self.failUnlessEqual(checkbox_result, EXPECTED_SELECTED_CHECKBOX, 'Basic "checkbox" field misrendered as \n`%s`, not \n`%s`' % (checkbox_result, EXPECTED_SELECTED_CHECKBOX));
		
	def test_title(self):
		"""
		Test textfield item rendering.
		"""
		title = self.form['title']
		
		title_result = self.theme.form_textfield('node-form', title)
		self.failUnlessEqual(title_result, EXPECTED_TITLE, 'Basic "title" field misrendered as \n`%s`, not \n`%s`' % (title_result, EXPECTED_TITLE));
		
	def test_prefix_suffix(self):
		"""
		Test form item prefix and suffix rendering.
		"""
		title = self.form['title']
		title(prefix='##PREFIX##', suffix='##SUFFIX##')
		
		titlefield_result = self.theme.form_element('node-form', title)
		titlefield_check = EXPECTED_ELEMENT % ('title', (EXPECTED_LABEL % title.label) + ('##PREFIX##%s##SUFFIX##' % EXPECTED_TITLE) + (EXPECTED_HELP % title.help))
		self.failUnlessEqual(titlefield_result, titlefield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (titlefield_result, titlefield_check));
		
	def test_title_field(self):
		"""
		Test textfield/form item rendering.
		"""
		title = self.form['title']
		
		titlefield_result = self.theme.form_element('node-form', title)
		titlefield_check = EXPECTED_ELEMENT % ('title', (EXPECTED_LABEL % title.label) + EXPECTED_TITLE + (EXPECTED_HELP % title.help))
		self.failUnlessEqual(titlefield_result, titlefield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (titlefield_result, titlefield_check));

	def test_errors(self):
		"""
		Test form errors and related rendering.
		"""
		self.form.set_error('title', 'There is an error in the title field.')
		title = self.form['title']
		
		titlefield_result = self.theme.form_element('node-form', title)
		titlefield_check = EXPECTED_ERROR_ELEMENT % ('title', (EXPECTED_LABEL % title.label) + EXPECTED_TITLE + (EXPECTED_HELP % title.help))
		self.failUnlessEqual(titlefield_result, titlefield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (titlefield_result, titlefield_check));

	def test_category(self):
		"""
		Test select rendering.
		"""
		category = self.form['category']
		
		category_result = self.theme.form_select('node-form', category)
		self.failUnlessEqual(category_result, EXPECTED_CATEGORY, 'Basic "category" field misrendered as \n`%s`, not \n`%s`' % (category_result, EXPECTED_CATEGORY));
		
	def test_other_category(self):
		"""
		Test multiple select rendering.
		"""
		other_category = self.form['other_category']
		
		category_result = self.theme.form_select('node-form', other_category)
		
		self.failUnlessEqual(category_result, EXPECTED_MULTIPLE_CATEGORY, '"other_category" field misrendered as \n`%s`, not \n`%s`' % (category_result, EXPECTED_MULTIPLE_CATEGORY));
		
	def test_body(self):
		"""
		Test textarea rendering.
		"""
		body = self.form['body']
		
		body_result = self.theme.form_textarea('node-form', body)
		self.failUnlessEqual(body_result, EXPECTED_BODY, 'Basic "body" field misrendered as \n`%s`, not \n`%s`' % (body_result, EXPECTED_BODY));
		
	def test_body_field(self):
		"""
		Test textarea/form item rendering.
		"""
		body = self.form['body']
		
		bodyfield_result = self.theme.form_element('node-form', body)
		bodyfield_check = EXPECTED_ELEMENT % ('body', (EXPECTED_LABEL % body.label) + EXPECTED_BODY + (EXPECTED_HELP % body.help))
		self.failUnlessEqual(bodyfield_result, bodyfield_check, '"body" form field misrendered as \n`%s`, not \n`%s`' % (bodyfield_result, bodyfield_check));
	
	def test_submit(self):
		"""
		Test button rendering.
		"""
		submit = self.form['submit']
		
		submit_result = self.theme.form_submit('node-form', submit)
		self.failUnlessEqual(submit_result, EXPECTED_SUBMIT, 'Basic "submit" field misrendered as \n`%s`, not \n`%s`' % (submit_result, EXPECTED_SUBMIT));
		
	def test_submit_field(self):
		"""
		Test button/form item rendering.
		"""
		submit = self.form['submit']
		
		submitfield_result = self.theme.form_element('node-form', submit)
		submitfield_check = EXPECTED_ELEMENT % ('submit', EXPECTED_SUBMIT)
		self.failUnlessEqual(submitfield_result, submitfield_check, '"title" form field misrendered as \n`%s`, not \n`%s`' % (submitfield_result, submitfield_check));

