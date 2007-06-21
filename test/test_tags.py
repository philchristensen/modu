#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest, difflib

from dathomir.util import tags

class TagsTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_input(self):
		tag = tags.input(_class='inputfield', type='password', size=30)
		expected = '<input class="inputfield" size="30" type="password" />'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_select(self):
		option = tags.option(value="some-value")['some-label']
		tag = tags.select(name="select_field")[option]
		expected = '<select name="select_field"><option value="some-value">some-label</option></select>'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_longer_select(self):
		option = tags.option(value="some-value")['some-label']
		option2 = tags.option(value="some-other-value")['some-other-label']
		tag = tags.select(name="select_field")[(option, option2)]
		expected = '<select name="select_field"><option value="some-value">some-label</option><option value="some-other-value">some-other-label</option></select>'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_checkbox(self):
		tag = tags.input(type='checkbox', value=1, checked=None)
		expected = '<input type="checkbox" value="1" checked />'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
if __name__ == "__main__":
	unittest.main()