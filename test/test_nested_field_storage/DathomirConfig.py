#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.app import handler
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
		tree = self.req.dathomir.tree
		if(tree.unparsed_path and tree.unparsed_path[0] == 'test_basic'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one']['two']['three'], 'value 3', 'Did not find "value 3" where expected.')
	
	def test_broken(self):
		tree = self.req.dathomir.tree
		if(tree.unparsed_path and tree.unparsed_path[0] == 'test_broken'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one'], 'value 1', 'Did not find "value 1" where expected.')
			self.assertEqual(fields['test[one][two][three]'], 'value 3', 'Did not find "value 3" where expected.')
	
app.base_path = '/dathomir/test/test_nested_field_storage'
app.db_url = None
app.session_class = None
app.initialize_store = False
app.activate(test.TestResource(NestedFieldStorageTestCase))
