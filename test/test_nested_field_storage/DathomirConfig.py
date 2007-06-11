#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.config import handler
from dathomir import config
from dathomir.util import form, test

import unittest

class NestedFieldStorageTestCase(unittest.TestCase):
	req = None
	
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_basic(self):
		if(self.req.tree.unparsed_path and self.req.tree.unparsed_path[0] == 'test_basic'):
			fields = form.NestedFieldStorage(self.req)
			self.assertEqual(fields['test']['one']['two']['three'], 'value 3', 'Did not find "value 3" where expected.')
	
	def test_broken(self):
		if(self.req.tree.unparsed_path and self.req.tree.unparsed_path[0] == 'test_broken'):
			fields = form.NestedFieldStorage(self.req)
			self.req.log_error(repr(fields))
			self.assertEqual(fields['test']['one'], 'value 1', 'Did not find "value 1" where expected.')
			self.assertEqual(fields['test[one][two][three]'], 'value 3', 'Did not find "value 3" where expected.')
	
config.base_path = '/dathomir/test/test_nested_field_storage'
config.db_url = None
config.session_class = None
config.initialize_store = False
config.activate(test.TestResource(NestedFieldStorageTestCase))
