# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu.util import tags

class TagsTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_a_stub(self):
		tag = tags.a(href='http://www.example.com', __no_close=True)
		expected = '<a href="http://www.example.com">'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_input(self):
		tag = tags.input(_class='inputfield', type='password', size=30)
		expected = '<input class="inputfield" size="30" type="password" />'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_input_quoted(self):
		tag = tags.input(_class='inputfield', type='password', value="This value has \"quotes\"", size=30)
		expected = '<input class="inputfield" size="30" type="password" value="This value has &quot;quotes&quot;" />'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_select(self):
		option = tags.option(value="some-value")['some-label']
		tag = tags.select(name="select_field")[option]
		expected = '<select name="select_field"><option value="some-value">some-label</option></select>'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_select_trick(self):
		options = {1:'some-label', 2:'other-label'}
		opt_tags = map(lambda(item): tags.option(value=item[0])[item[1]], options.items())
		tag = tags.select(name="select_field")[opt_tags]
		expected = '<select name="select_field"><option value="1">some-label</option><option value="2">other-label</option></select>'
		self.assertEqual(str(tag), expected, "Got '%s' instead of '%s'" % (str(tag), expected))
	
	def test_select_trick2(self):
		options = ['some-label', 'other-label']
		opt_tags = map(lambda(item): tags.option(value=item[0])[item[1]], [(i,options[i]) for i in range(len(options))])
		tag = tags.select(name="select_field")[opt_tags]
		expected = '<select name="select_field"><option value="0">some-label</option><option value="1">other-label</option></select>'
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
	
