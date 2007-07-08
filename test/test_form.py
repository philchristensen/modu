#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import form

from twisted.trial import unittest

class FormTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_basic_form(self):
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['title'](type='textfield', title='Title', required=True, description='This is the title field')
		self.assertEqual(frm['title'].attributes['type'], 'textfield', "Didn't find correct type.")
		self.assertEqual(frm['title'].attributes['title'], 'Title', "Didn't find correct title.")
		self.assertEqual(frm.attributes['enctype'], 'multipart/form-data', "Didn't find correct enctype.")
	
	def test_fieldset(self):
		frm = form.FormNode('test-form')
		frm['title-area'](type='fieldset', collapsed=False, collapsible=True, title='Title Area')
		frm['title-area']['title'](type='textfield', title='Title', required=True, description='This is the title field')
		
		self.assertEqual(frm['title-area'].attributes['type'], 'fieldset', "Didn't find correct type.")
		self.assertEqual(frm['title-area'].children['title'], frm['title-area']['title'], "Didn't find nested child.")

