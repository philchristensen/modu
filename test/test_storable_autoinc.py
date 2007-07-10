#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, time, sys

from MySQLdb import cursors

from modu import persist
from modu.persist import storable

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
		self.store = persist.Store.get_store()
		if not(self.store):
			self.connection = MySQLdb.connect('localhost', 'modu', 'modu', 'modu')
			self.store = persist.Store(self.connection, debug_file=sys.stderr)
		self.store.ensure_factory('autoinc_table', guid_table=None)
		
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
		
		t = self.store.load_one('autoinc_table', {'id':saved_id})
		
		self.failUnlessEqual(s.content, t.content, 'Content changed during save/load cycle')
	
