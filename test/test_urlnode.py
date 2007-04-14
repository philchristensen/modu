#!/usr/bin/env python

# dathomir
# Copyright (C) 1999-2006 Phil Christensen
#
# See LICENSE for details

import unittest

from dathomir.util import urlnode

class URLNodeTestCase(unittest.TestCase):
	def setUp(self):
		self.tree = urlnode.URLNode('ROOT')
	
	def tearDown(self):
		pass
	
	def test_urlnode(self):
		self.tree.register('/', 'SLASH')
		self.tree.register('/one', 'ONE')
		self.tree.register('/one/two', 'TWO')
		self.tree.register('/three', 'THREE')
		self.tree.register('/this/is/a/long/url', 'LONG')
		
		result = self.tree.parse('/one/and/some/extra/crud')
		assert(result == 'ONE', "Didn't find 'ONE' where I expected")
		
		result = self.tree.parse('/one/two/some/extra/crud')
		assert(result == 'TWO', "Didn't find 'TWO' where I expected")
		
		result = self.tree.parse('/three')
		assert(result == 'THREE', "Didn't find 'THREE' where I expected")
		
		result = self.tree.parse('/something/else')
		assert(result == 'SLASH', "Didn't find 'SLASH' where I expected")
		
		result = self.tree.parse('/this/is/a/long/url')
		assert(result == 'LONG', "Didn't find 'LONG' where I expected")

if __name__ == "__main__":
	unittest.main()
