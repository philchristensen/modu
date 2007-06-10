#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id: test_urlnode.py 269 2007-06-07 19:26:34Z phil $
#
# See LICENSE for details

from dathomir.util import form

import unittest

class FormTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_basic_form(self):
		frm = form.FormNode('test-form')
		frm(enctype="multipart/form-data")
		frm['title'](type='textfield', title='Title', required=True, description='This is the title field')
	
	def test_fieldset(self):
		frm = form.FormNode('test-form')
		frm['title-area'](type='fieldset', collapsed=False, collapsible=True, title='Title Area')
		frm['title-area']['title'](type='textfield', title='Title', required=True, description='This is the title field')

if __name__ == "__main__":
	unittest.main()
