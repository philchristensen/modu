# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu import persist

class SQLTestCase(unittest.TestCase):
	def setUp(self):
		pass
	
	def tearDown(self):
		pass
	
	def test_build_delete(self):
		sql = persist.build_delete('table', {'col1':'col1_data', 'col2':'col2_data'});
		expecting = "DELETE FROM `table` WHERE `col1` = 'col1_data' AND `col2` = 'col2_data'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert(self):
		sql = persist.build_insert('table', {'col2':'col2_data', 'col1':persist.RAW("ENCRYPT('something')")});
		expecting = "INSERT INTO `table` (`col1`, `col2`) VALUES (ENCRYPT('something'), 'col2_data')"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert_dot_syntax(self):
		sql = persist.build_insert('db.table', {'col2':'col2_data', 'col1':persist.RAW("ENCRYPT('something')")});
		expecting = "INSERT INTO db.`table` (`col1`, `col2`) VALUES (ENCRYPT('something'), 'col2_data')"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_insert_raw(self):
		sql = persist.build_insert('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "INSERT INTO `table` (`col1`, `col2`) VALUES ('col1_data', 'col2_data')"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_replace(self):
		sql = persist.build_replace('table', {'col2':'col2_data', 'col1':'col1_data'});
		expecting = "REPLACE INTO `table` SET `col1` = 'col1_data', `col2` = 'col2_data'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_replace_raw(self):
		sql = persist.build_replace('table', {'col2':'col2_data', 'col1':persist.RAW("ENCRYPT('something')")});
		expecting = "REPLACE INTO `table` SET `col1` = ENCRYPT('something'), `col2` = 'col2_data'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
	
	def test_build_select_dot_syntax(self):
		sql = persist.build_select('db.table', {'t.col2':'col2_data', 's.col1':'col1_data'});
		expecting = "SELECT * FROM db.`table` WHERE s.`col1` = 'col1_data' AND t.`col2` = 'col2_data'"
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

	def test_build_select_raw(self):
		sql = persist.build_select('table', {'col1':persist.RAW("= ENCRYPT('something', SUBSTRING(col1,1,2))")});
		expecting = "SELECT * FROM `table` WHERE `col1`= ENCRYPT('something', SUBSTRING(col1,1,2))"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))

	def test_build_select_not(self):
		sql = persist.build_select('table', {'col1':persist.NOT("somestring")});
		expecting = "SELECT * FROM `table` WHERE `col1` <> 'somestring'"
		self.failUnlessEqual(sql, expecting, 'Got "%s" when expecting "%s"' % (sql, expecting))
