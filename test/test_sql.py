#!/usr/bin/env python

# dathomir
# Copyright (C) 1999-2006 Phil Christensen
#
# See LICENSE for details

import unittest

from dathomir import persist

class SQLTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_build_insert(self):
		sql = persist.build_insert('table', {'col1':'col1_data', 'col2':'col2_data'});
		assert(sql == "INSERT INTO table (`col1`, `col2`) VALUES ('col1_data', 'col2_data')",'Result INSERT statement wasn\'t as expected')
	
	def test_build_replace(self):
		sql = persist.build_insert('table', {'col1':'col1_data', 'col2':'col2_data'});
		assert(sql == "REPLACE INTO table SET `col1` = 'col1_data', `col2` = 'col2_data'",'Result REPLACE statement wasn\'t as expected')
	
	def test_build_select(self):
		sql = persist.build_select('table', {'col1':'col1_data', 'col2':'col2_data'});
		assert(sql == "SELECT * FROM table WHERE `col1` = 'col1_data' AND `col2` = 'col2_data'",'Result SELECT statement wasn\'t as expected')
	
	def test_build_select_order(self):
		sql = persist.build_select('table', {'col1':'col1_data', 'col2':'col2_data', '__order_by':'id DESC'});
		assert(sql == "SELECT * FROM table WHERE `col1` = 'col1_data' AND `col2` = 'col2_data' ORDER BY id DESC",'Result SELECT statement wasn\'t as expected')
	
	def test_build_select_distinct(self):
		sql = persist.build_select('table', {'col1':'col1_data', 'col2':'col2_data', '__select_keyword':'DISTINCT'});
		assert(sql == "SELECT DISTINCT * FROM table WHERE `col1` = 'col1_data' AND `col2` = 'col2_data'",'Result SELECT statement wasn\'t as expected')
	
	def test_build_select_in(self):
		sql = persist.build_select('table', {'col1':['col1_data', 'col2_data']});
		assert(sql == "SELECT * FROM table WHERE `col1` IN ('col1_data', 'col2_data')",'Result SELECT statement wasn\'t as expected')
	
	def test_build_select_in_limit(self):
		sql = persist.build_select('table', {'col1':['col1_data', 'col2_data'], '__limit':5});
		assert(sql == "SELECT * FROM table WHERE `col1` IN ('col1_data', 'col2_data') LIMIT 5",'Result SELECT statement wasn\'t as expected')
	
	def test_build_select_none(self):
		sql = persist.build_select('table', {'col1':None});
		assert(sql == "SELECT * FROM table WHERE ISNULL(`col1`)",'Result SELECT statement wasn\'t as expected')

if __name__ == "__main__":
	unittest.main()
