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

CREATE TABLE IF NOT EXISTS `guid` (
  `guid` bigint(20) unsigned NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

REPLACE INTO `guid` VALUES (1);
"""

class StorableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.get_store()
		if not(self.store):
			self.connection = MySQLdb.connect('localhost', 'modu', 'modu', 'modu')
			self.store = persist.Store(self.connection)
		
		global TEST_TABLES
		cur = self.store.get_cursor()
		for sql in TEST_TABLES.split(";"):
			if(sql.strip()):
				cur.execute(sql)
	
	def tearDown(self):
		pass
	
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
	
