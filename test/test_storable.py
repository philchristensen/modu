#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, time, sys, copy

from MySQLdb import cursors

from modu import persist
from modu.persist import storable

from twisted.trial import unittest

"""
CREATE DATABASE modu;
GRANT ALL ON modu.* TO modu@localhost IDENTIFIED BY 'modu';
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

DROP TABLE IF EXISTS `subpage`;
CREATE TABLE IF NOT EXISTS `subpage` (
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
"""

class StorableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.Store.get_store()
		if not(self.store):
			self.connection = MySQLdb.connect('localhost', 'modu', 'modu', 'modu')
			self.store = persist.Store(self.connection, debug_file=sys.stderr)
		
		global TEST_TABLES
		cur = self.store.get_cursor()
		for sql in TEST_TABLES.split(";"):
			if(sql.strip()):
				cur.execute(sql)
	
	def tearDown(self):
		pass
	
	def test_create(self):
		self.store.ensure_factory('page', force=True)
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		self.failUnless(s.get_id(), 'Storable object has no id after being saved.')
		t = self.store.load_one('page', {'id':s.get_id()});
		
		self.failUnlessEqual(t.get_id(), s.get_id(), 'Column `id` changed in save/load cycle')
		self.failUnlessEqual(t.code, s.code, 'Column `code` changed in save/load cycle')
		self.failUnlessEqual(t.content, s.content, 'Column `content` changed in save/load cycle')
		self.failUnlessEqual(t.title, s.title, 'Column `title` changed in save/load cycle')
	
	def test_destroy(self):
		self.store.ensure_factory('page', force=True)
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		saved_id = s.get_id()
		self.failUnless(saved_id, 'Storable object has no id after being saved.')
		
		self.store.destroy(s)
		t = self.store.load_one('page', {'id':saved_id});
		
		self.failIf(t, 'Storable object was not properly destroyed.')
		self.failIf(s.get_id(), 'Storable object still has an id after being destroyed.')
	
	def test_subclass(self):
		self.store.ensure_factory('page', TestStorable, force=True)
		
		s = TestStorable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		self.failUnless(s.get_id(), 'Storable object has no id after being saved.')
		t = self.store.load_one('page', {'id':s.get_id()});
		
		self.failUnless(isinstance(t, TestStorable), "Loaded object wasn't of the correct type: %r" % t)
		self.failUnlessEqual(t.get_id(), s.get_id(), 'Column `id` changed in save/load cycle')
		self.failUnlessEqual(t.code, s.code, 'Column `code` changed in save/load cycle')
		self.failUnlessEqual(t.content, s.content, 'Column `content` changed in save/load cycle')
		self.failUnlessEqual(t.title, s.title, 'Column `title` changed in save/load cycle')
	
	def test_save_related(self):
		self.store.ensure_factory('page', TestStorable, force=True)
		
		s = TestStorable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		s.populate_related_items()
		# at this point, the related items are saved,
		# so we can edit them
		self.store.save(s)
		
		for item in s._related:
			item.content = 'updated content'
		
		self.store.save(s)
	
		for item in s._related:
			self.failUnlessEqual(item.content, 'updated content')
	
	def test_destroy_related(self):
		self.store.ensure_factory('page', TestStorable, force=True)
		self.store.ensure_factory('subpage', force=True)
		
		s = TestStorable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		s.populate_related_items()
		print s.get_related_storables()
		# at this point, the related items are saved,
		# so we can DESTROY them! RARRRRGH!!!
		self.store.save(s)
		print s.get_related_storables()
		self.store.destroy(s, True)
	
		orig = self.store.load_one('page', {'code':'url-code'})
		self.failUnless(orig is None, "Found 'url-code' object after destroying it.")
		
		page1 = self.store.load_one('subpage', {'code':'__sample-1__'})
		self.failUnless(page1 is None, "Found '__sample-1__' object after destroying it.")
		
		page2 = self.store.load_one('subpage', {'code':'__sample-2__'})
		self.failUnless(page2 is None, "Found '__sample-2__' object after destroying it.")
		
		page3 = self.store.load_one('subpage', {'code':'__sample-3__'})
		self.failUnless(page3 is None, "Found '__sample-3__' object after destroying it.")
	

class TestStorable(storable.Storable):
	def __init__(self):
		super(TestStorable, self).__init__('page')
		self._related = []
	
	def populate_related_items(self):
		store = persist.Store.get_store()
		store.ensure_factory('subpage', force=True)
		
		page1 = store.load_one('subpage', {'code':'__sample-1__'})
		if(page1 is None):
			page1 = storable.Storable('subpage')
			page1.code = '__sample-1__'
			page1.content = 'test content'
		
		page2 = store.load_one('subpage', {'code':'__sample-2__'})
		if(page2 is None):
			page2 = storable.Storable('subpage')
			page2.code = '__sample-2__'
			page2.content = 'test content'
		
		page3 = store.load_one('subpage', {'code':'__sample-3__'})
		if(page3 is None):
			page3 = storable.Storable('subpage')
			page3.code = '__sample-3__'
			page3.content = 'test content'
		
		self._related = [page1, page2, page3]
	
	def sample_function(self):
		return True
	
	def get_related_storables(self):
		return copy.copy(self._related)
		