#!/usr/bin/env python

# dathomir
# Copyright (C) 1999-2006 Phil Christensen
#
# See LICENSE for details

import unittest
from dathomir import persist

class SQLTestCase(unittest.TestCase):
	"""
	These tests are practically worthless right now, since there really
	is no predicting what the output order of a hash table is.
	
	It might be worth switching to the alternate interpolation mechanism
	and using %(key) to force positions.
	"""
	
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_build_insert(self):
		sql = persist.build_insert('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "INSERT INTO `table` (`col1`, `col2`) VALUES ('col1_data', 'col2_data')"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_replace(self):
		sql = persist.build_replace('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "REPLACE INTO `table` SET `col1` = 'col1_data', `col2` = 'col2_data'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select(self):
		sql = persist.build_select('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "SELECT * FROM `table` WHERE `col1` = 'col1_data' AND `col2` = 'col2_data'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_order(self):
		sql = persist.build_select('table', {'col1':'col1_data', 'col2':'col2_data', '__order_by':'id DESC'});
		expecting = "SELECT * FROM `table` WHERE `col1` = 'col1_data' AND `col2` = 'col2_data' ORDER BY id DESC"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_distinct(self):
		sql = persist.build_select('table', {'col1':'col1_data', 'col2':'col2_data', '__select_keyword':'DISTINCT'});
		expecting = "SELECT DISTINCT * FROM `table` WHERE `col1` = 'col1_data' AND `col2` = 'col2_data'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_in(self):
		sql = persist.build_select('table', {'col1':['col1_data', 'col2_data']});
		expecting = "SELECT * FROM `table` WHERE `col1` IN ('col1_data', 'col2_data')"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_in_limit(self):
		sql = persist.build_select('table', {'col1':['col1_data', 'col2_data'], '__limit':5});
		expecting = "SELECT * FROM `table` WHERE `col1` IN ('col1_data', 'col2_data') LIMIT 5"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_none(self):
		sql = persist.build_select('table', {'col1':None});
		expecting = "SELECT * FROM `table` WHERE ISNULL(`col1`)"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))

if __name__ == "__main__":
	unittest.main()
