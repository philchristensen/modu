#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, unittest, time, os, cStringIO
from MySQLdb import cursors

from dathomir.persist import storable
from dathomir.config import handler
from dathomir import config, resource, persist

"""
CREATE DATABASE dathomir;
GRANT ALL ON dathomir.* TO dathomir@localhost IDENTIFIED BY 'dathomir';
"""

TEST_TABLES = """
DROP TABLE IF EXISTS `session`;
CREATE TABLE session (
  id varchar(255) NOT NULL default '',
  user_id bigint(20) unsigned NOT NULL,
  created int(11) NOT NULL default '0',
  accessed int(11) NOT NULL default '0',
  timeout int(11) NOT NULL default '0',
  data binary,
  PRIMARY KEY (id),
  KEY user_idx (user_id),
  KEY accessed_idx (accessed),
  KEY timeout_idx (timeout),
  KEY expiry_idx (accessed, timeout)
) DEFAULT CHARACTER SET utf8;
"""

class DbSessionTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.get_store()
		if not(self.store):
			self.connection = MySQLdb.connect('localhost', 'dathomir', 'dathomir', 'dathomir')
			self.store = persist.Store(self.connection)
		cur = self.store.get_cursor()
		cur.execute(TEST_TABLES)
	
	def tearDown(self):
		pass
	
	def test_create(self):
		raise RuntimeError('crash.')
	
class SessionTestResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, request):
		stream = cStringIO.StringIO()
		runner = unittest.TextTestRunner(stream=stream, descriptions=1, verbosity=1)
		loader = unittest.TestLoader()
		test = loader.loadTestsFromTestCase(DbSessionTestCase)
		runner.run(test)
		self.add_slot('content', stream.getvalue())
		stream.close()
	
	def get_content_type(self, request):
		return 'text/html'
	
	def get_template(self, request):
		return 'page.html.tmpl' 

config.base_path = '/dathomir/test/test_session'
config.activate(SessionTestResource())
