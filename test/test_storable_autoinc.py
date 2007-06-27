#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, unittest, time, sys

from MySQLdb import cursors

from dathomir import persist
from dathomir.persist import storable

"""
CREATE DATABASE dathomir;
GRANT ALL ON dathomir.* TO dathomir@localhost IDENTIFIED BY 'dathomir';
"""

TEST_TABLES = """
DROP TABLE IF EXISTS `autoinc_table`;
CREATE TABLE `autoinc_table` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `content` text NOT NULL,
  PRIMARY KEY  (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
"""

class StorableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.get_store()
		if not(self.store):
			self.connection = MySQLdb.connect('localhost', 'dathomir', 'dathomir', 'dathomir')
			self.store = persist.Store(self.connection, guid_table=None, debug_file=sys.stderr)
		
		global TEST_TABLES
		cur = self.store.get_cursor()
		for sql in TEST_TABLES.split(";"):
			if(sql.strip()):
				cur.execute(sql)
	
	def tearDown(self):
		pass
	
	def test_autoinc(self):
		s = storable.Storable('autoinc_table')
		s.content = 'The quick brown fox jumps over the lazy dog.'
		
		self.store.save(s)
		
		self.failUnlessEqual(s.get_id(), 1, 'Autoincrement IDs are broken')
		
		s.content = 'Some other content for my object'
		self.store.save(s)
		saved_id = s.get_id()
		self.failUnlessEqual(saved_id, 1, 'Autoincrement IDs are broken')
		
		self.store.ensure_factory('autoinc_table')
		t = self.store.load_one('autoinc_table', {'id':saved_id})
		
		self.failUnlessEqual(s.content, t.content, 'Content changed during save/load cycle')
	
if __name__ == "__main__":
	unittest.main()
