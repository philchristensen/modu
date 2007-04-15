#!/usr/bin/env python

# dathomir
# Copyright (C) 1999-2006 Phil Christensen
#
# See LICENSE for details

import unittest

from dathomir.persist import storable


class StorableTestCase(unittest.TestCase):
	def setUp(self):
	
	def tearDown(self):
		self.cursor.close()
		self.conn.close()
	
	def test_insert(self):
		pass
	
	def test_update(self):
		pass
		
	def test_delete(self):
		pass
	
if __name__ == "__main__":
	unittest.main()
