# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

import MySQLdb, time, sys

from MySQLdb import cursors

from modu import persist
from modu.persist import storable, dbapi

from twisted.trial import unittest

"""
CREATE DATABASE modu;
GRANT ALL ON modu.* TO modu@localhost IDENTIFIED BY 'modu';
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
		pool = dbapi.connect('MySQLdb://modu:modu@localhost/modu')
		self.store = persist.Store(pool)
		#self.store.debug_file = sys.stderr
		self.store.ensure_factory('autoinc_table', guid_table=None)
		
		global TEST_TABLES
		for sql in TEST_TABLES.split(";"):
			if(sql.strip()):
				self.store.pool.runOperation(sql)
	
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
		
		t = self.store.load_one('autoinc_table', {'id':saved_id})
		
		self.failUnlessEqual(s.content, t.content, 'Content changed during save/load cycle')
	
