#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest

from modu.persist import storable
from modu.util import test
from modu.web import resource, session
from modu import persist

from modu.web.app import ISite
from zope.interface import classProvides
from twisted import plugin

"""
CREATE DATABASE modu;
GRANT ALL ON modu.* TO modu@localhost IDENTIFIED BY 'modu';
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
		cur = self.req['modu.db'].cursor()
		cur.execute(TEST_TABLES)
	
	def tearDown(self):
		pass
	
	def test_create(self):
		sess = session.DbSession(self.req, self.req['modu.db'])
		sess['test_data'] = 'test'
		sess.save()
		
		saved_sess = session.DbSession(self.req, self.req['modu.db'], sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'test', "Session data was not saved properly.")
		self.failUnlessEqual(int(saved_sess._created), int(sess._created), "Session created date changed during save/load cycle.")
	
	def test_noclobber(self):
		sessid = session.generate_token()
		sess = session.DbSession(self.req, self.req['modu.db'], sessid)
		sess2 = session.DbSession(self.req, self.req['modu.db'], sessid)
		sess['test_data'] = 'something'
		sess.save()
		sess2.save()
		
		saved_sess = session.DbSession(self.req, self.req['modu.db'], sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'something', "Session data was not saved properly.")

class TestSessionSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def configure_app(self, application):
		application.base_domain = 'localhost:8888'
		application.base_path = '/modu/test/test_session'
		application.session_class = None
		application.activate(test.TestResource(DbSessionTestCase))
