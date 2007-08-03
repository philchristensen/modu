#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import app
from modu.util import form, test

import unittest

from modu.web.app import ISite
from zope.interface import classProvides
from twisted import plugin

class NestedFieldStorageTestCase(unittest.TestCase):
	req = None
	
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_basic(self):
		tree = self.req['modu.tree']
		if(tree.postpath and tree.postpath[0] == 'test_basic'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one']['two']['three'].value, 'value 3', 'Did not find "value 3" where expected.')
			self.assertEqual(len(fields.__dict__['list']), 2, 'Found %d fields in NestedFieldStorage::list, expected 2.' % len(fields.__dict__['list']))
	
	def test_broken(self):
		tree = self.req['modu.tree']
		if(tree.postpath and tree.postpath[0] == 'test_broken'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one'].value, 'value 1', 'Did not find "value 1" where expected.')
			self.assertEqual(fields['test[one][two][three]'].value, 'value 3', 'Did not find "value 3" where expected.')
			self.assertEqual(len(fields.__dict__['list']), 3, 'Found %d fields in NestedFieldStorage::list, expected 3.' % len(fields.__dict__['list']))
	
	def test_normal(self):
		tree = self.req['modu.tree']
		if(tree.postpath and tree.postpath[0] == 'test_normal'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['sample-form']['title'].value, 'title field data', 'Did not find sample-form[title] data.')
			self.assertEqual(fields['sample-form']['body'].value, 'body field data', 'Did not find sample-form[body] data.')
			self.assertEqual(fields['test_normal'].value, 'test_normal_multipart', 'Found "%s" expecting "test_normal_multipart".' % fields['test_normal'].value)
			self.assertEqual(len(fields.__dict__['list']), 3, 'Found %d fields in NestedFieldStorage::list, expected 3.' % len(fields.__dict__['list']))

class TestSessionSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, application):
		application.base_path = '/modu/test/test_nested_field_storage'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(test.TestResource(NestedFieldStorageTestCase))
