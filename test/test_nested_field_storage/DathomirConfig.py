#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.web.modpython import handler
from dathomir import app
from dathomir.util import form, test

import unittest

class NestedFieldStorageTestCase(unittest.TestCase):
	req = None
	
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_basic(self):
		tree = self.req['dathomir.tree']
		if(tree.unparsed_path and tree.unparsed_path[0] == 'test_basic'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one']['two']['three'].value, 'value 3', 'Did not find "value 3" where expected.')
			self.assertEqual(len(fields.__dict__['list']), 2, 'Found more fields in NestedFieldStorage::list than expected.')
	
	def test_broken(self):
		tree = self.req['dathomir.tree']
		if(tree.unparsed_path and tree.unparsed_path[0] == 'test_broken'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one'].value, 'value 1', 'Did not find "value 1" where expected.')
			self.assertEqual(fields['test[one][two][three]'].value, 'value 3', 'Did not find "value 3" where expected.')
			self.assertEqual(len(fields.__dict__['list']), 1, 'Found more fields in NestedFieldStorage::list than expected.')
	
	def test_normal(self):
		tree = self.req['dathomir.tree']
		if(tree.unparsed_path and tree.unparsed_path[0] == 'test_normal'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['sample-form']['title'].value, 'title field data', 'Did not find sample-form[title] data.')
			self.assertEqual(fields['sample-form']['body'].value, 'body field data', 'Did not find sample-form[body] data.')
			self.assertEqual(len(fields.__dict__['list']), 1, 'Found more fields in NestedFieldStorage::list than expected.')

app.base_url = '/dathomir/test/test_nested_field_storage'
app.db_url = None
app.session_class = None
app.initialize_store = False
app.activate(test.TestResource(NestedFieldStorageTestCase))
