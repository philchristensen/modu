#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest, time

from MySQLdb import cursors

from dathomir import persist
from dathomir.persist import storable

"""
CREATE DATABASE dathomir;
GRANT ALL ON dathomir.* TO dathomir@localhost IDENTIFIED BY 'dathomir';
"""

TEST_TABLES = """
DROP TABLE IF EXISTS `page`;
CREATE TABLE IF NOT EXISTS `page` (
  `id` bigint(20) unsigned NOT NULL default 0,
  `code` varchar(128) NOT NULL default '',
  `content` text NOT NULL,
  `title` varchar(64) NOT NULL default '',
  `created_date` int(11) NOT NULL default '0',
  `modified_date` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `guid`;
CREATE TABLE IF NOT EXISTS `guid` (
  `guid` bigint(20) unsigned NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `guid` VALUES (1);
"""

class StorableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.get_store()
		if not(self.store):
			self.store = persist.Store(user='dathomir', password='dathomir', db='dathomir')
		cur = self.store.get_cursor()
		cur.execute(TEST_TABLES)
	
	def test_create(self):
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		self.failUnless(s.get_id(), 'Storable object has no id after being saved.')
		self.store.ensure_factory('page')
		t = self.store.load_one('page', {'id':s.get_id()});
		
		self.failUnlessEqual(t.get_id(), s.get_id(), 'Column `id` changed in save/load cycle')
		self.failUnlessEqual(t.code, s.code, 'Column `code` changed in save/load cycle')
		self.failUnlessEqual(t.content, s.content, 'Column `content` changed in save/load cycle')
		self.failUnlessEqual(t.title, s.title, 'Column `title` changed in save/load cycle')
	
	def test_destroy(self):
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		saved_id = s.get_id()
		self.failUnless(saved_id, 'Storable object has no id after being saved.')
		
		self.store.destroy(s)
		self.store.ensure_factory('page')
		t = self.store.load_one('page', {'id':saved_id});
		
		self.failIf(t, 'Storable object was not properly destroyed.')
		self.failIf(s.get_id(), 'Storable object still has an id after being destroyed.')
	
	def tearDown(self):
		pass
	
if __name__ == "__main__":
	unittest.main()