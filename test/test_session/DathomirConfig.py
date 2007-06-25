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
from dathomir import app, resource, persist, session

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
	
app.base_url = '/dathomir/test/test_session'
app.session_class = None
app.activate(test.TestResource(DbSessionTestCase))
