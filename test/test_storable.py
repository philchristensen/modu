#!/usr/bin/env python

# dathomir
# Copyright (C) 1999-2006 Phil Christensen
#
# See LICENSE for details

import unittest, time

from dathomir import persist
from dathomir.persist import storable

"""
CREATE DATABASE dathomir;
GRANT ALL ON dathomir.* TO dathomir@localhost IDENTIFIED BY 'dathomir';
"""

TEST_TABLES = """
DROP TABLE IF EXISTS `page`;
CREATE TABLE IF NOT EXISTS `page` (
  `id` bigint(20) unsigned NOT NULL auto_increment,
  `code` varchar(128) NOT NULL default '',
  `content` text NOT NULL,
  `title` varchar(64) NOT NULL default '',
  `created_date` int(11) NOT NULL default '0',
  `modified_date` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;
"""

class StorableTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.Store(user='dathomir', password='dathomir', db='dathomir')
		self.store.cursor.execute(TEST_TABLES)
	
	def test_create(self):
		s = storable.Storable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
	
	def tearDown(self):
		pass
	
if __name__ == "__main__":
	unittest.main()
