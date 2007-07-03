#!/usr/bin/env python

# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest

from modu.persist import storable, RAW
from modu.util import test
from modu.web import resource, session, user
from modu import persist

from modu.web.app import ISite
from zope.interface import classProvides
from twisted import plugin

"""
CREATE DATABASE modu;
GRANT ALL ON modu.* TO modu@localhost IDENTIFIED BY 'modu';
"""

TEST_TABLES = ["""
CREATE TABLE IF NOT EXISTS `session` (
  `id` varchar(255),
  `user_id` bigint(20),
  `created` int(11),
  `accessed` int(11),
  `timeout` int(11),
  `data` BLOB,
  PRIMARY KEY (id),
  KEY `user_idx` (`user_id`),
  KEY `accessed_idx` (`accessed`),
  KEY `timeout_idx` (`timeout`),
  KEY `expiry_idx` (`accessed`, `timeout`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;
""","""
CREATE TABLE IF NOT EXISTS `guid` (
  `guid` bigint(20) unsigned
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;
"""]

class DbSessionTestCase(unittest.TestCase):
	req = None
	
	def setUp(self):
		cur = self.req['modu.db'].cursor()
		for sql in TEST_TABLES:
			cur.execute(sql)
	
	def test_create(self):
		sess = session.DbUserSession(self.req, self.req['modu.db'])
		sess['test_data'] = 'test'
		sess.save()
		
		saved_sess = session.DbUserSession(self.req, self.req['modu.db'], sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'test', "Session data was not saved properly.")
		#self.failUnlessEqual(int(saved_sess._created), int(sess._created), "Session created date changed during save/load cycle.")
	
	def test_noclobber(self):
		sessid = session.generate_token()
		sess = session.DbUserSession(self.req, self.req['modu.db'], sessid)
		sess2 = session.DbUserSession(self.req, self.req['modu.db'], sessid)
		sess['test_data'] = 'something'
		sess.save()
		sess2.save()
		
		saved_sess = session.DbUserSession(self.req, self.req['modu.db'], sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'something', "Session data was not saved properly.")
		
		sess.delete()
		sess2.delete()
	
	def test_users(self):
		usr = user.User()
		usr.username = 'sampleuser'
		usr.first = 'Sample'
		usr.last = 'User'
		usr.crypt = RAW("ENCRYPT('%s')" % 'password')
		usr.save()
		
		sess = session.DbUserSession(self.req, self.req['modu.db'])
		sess.set_user(usr)
		sess.save()
		
		saved_sess = session.DbUserSession(self.req, self.req['modu.db'], sid=sess.id())
		saved_user = saved_sess.get_user()
		self.failUnlessEqual(saved_sess._user_id, sess._user_id, "Found user_id %s when expecting %d." % (saved_sess._user_id, sess._user_id))
		self.failUnlessEqual(saved_user.get_id(), usr.get_id(), "User ID changed during save/load cycle.")
		self.failUnlessEqual(saved_user.username, usr.username, "Username changed during save/load cycle.")
		
		saved_user.destroy()

class TestSessionSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def configure_app(self, application):
		application.base_domain = 'localhost:8888'
		application.base_path = '/modu/test/test_session'
		application.session_class = None
		application.activate(test.TestResource(DbSessionTestCase))
