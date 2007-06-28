#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest

from dathomir.persist import storable
from dathomir.web.modpython import handler
from dathomir.util import test
from dathomir.web import app, resource, session
from dathomir import persist

"""
CREATE DATABASE dathomir;
GRANT ALL ON dathomir.* TO dathomir@localhost IDENTIFIED BY 'dathomir';
"""

TEST_TABLES = """
CREATE TABLE IF NOT EXISTS `session`(
  id varchar(255) NOT NULL default '',
  user_id bigint(20) unsigned NOT NULL,
  created int(11) NOT NULL default '0',
  accessed int(11) NOT NULL default '0',
  timeout int(11) NOT NULL default '0',
  data BLOB,
  PRIMARY KEY (id),
  KEY user_idx (user_id),
  KEY accessed_idx (accessed),
  KEY timeout_idx (timeout),
  KEY expiry_idx (accessed, timeout)
) DEFAULT CHARACTER SET utf8;
"""

class DbSessionTestCase(unittest.TestCase):
	req = None
	
	def setUp(self):
		cur = self.req['dathomir.db'].cursor()
		cur.execute(TEST_TABLES)
	
	def tearDown(self):
		pass
	
	def test_create(self):
		sess = session.DbSession(self.req, self.req['dathomir.db'])
		sess['test_data'] = 'test'
		sess.save()
		
		saved_sess = session.DbSession(self.req, self.req['dathomir.db'], sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'test', "Session data was not saved properly.")
		self.failUnlessEqual(int(saved_sess._created), int(sess._created), "Session created date changed during save/load cycle.")
	
	def test_noclobber(self):
		sessid = session.generate_token()
		sess = session.DbSession(self.req, self.req['dathomir.db'], sessid)
		sess2 = session.DbSession(self.req, self.req['dathomir.db'], sessid)
		sess['test_data'] = 'something'
		sess.save()
		sess2.save()
		
		saved_sess = session.DbSession(self.req, self.req['dathomir.db'], sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'something', "Session data was not saved properly.")
	
app.base_url = '/dathomir/test/test_session'
app.session_class = None
app.activate(test.TestResource(DbSessionTestCase))
