# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu.persist import storable, RAW, Store, adbapi
from modu.util import test, message
from modu.web import session, user, app
from modu import persist

TEST_TABLES = """
DROP TABLE IF EXISTS `session`;
CREATE TABLE `session` (
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

DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` bigint(20),
  `username` varchar(255),
  `first` varchar(255),
  `last` varchar(255),
  `crypt` varchar(255),
  PRIMARY KEY (id),
  UNIQUE KEY `username_idx` (`username`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;

DROP TABLE IF EXISTS `guid`;
CREATE TABLE `guid` (
  `guid` bigint(20) unsigned
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;
"""

class DbSessionTestCase(unittest.TestCase):
	def setUp(self):
		store = Store.get_store()
		if not(store):
			store = persist.Store(adbapi.connect('MySQLdb://modu:modu@localhost/modu'))
		
		global TEST_TABLES
		for sql in TEST_TABLES.split(";"):
			if(sql.strip()):
				try:
					store.pool.runOperation(sql)
				except store.pool.dbapi.Warning:
					pass
		
		self.store = store
	
	def get_request(self):
		environ = test.generate_test_wsgi_environment()
		environ['REQUEST_URI'] = '/app-test/test-resource'
		environ['SCRIPT_FILENAME'] = ''
		environ['HTTP_HOST'] = '____basic-test-domain____:1234567'
		environ['SERVER_NAME'] = '____basic-test-domain____'
		environ['HTTP_PORT'] = '1234567'
		
		application = app.get_application(environ)
		self.failIf(application is  None, "Didn't get an application object.")
		
		req = app.configure_request(environ, application)
		req['modu.store'] = self.store
		return req
	
	def test_create(self):
		req = self.get_request()
		
		sess = session.DbUserSession(req, self.store.pool)
		sess['test_data'] = 'test'
		sess.save()
		
		saved_sess = session.DbUserSession(req, self.store.pool, sid=sess.id())
		self.failUnlessEqual(saved_sess.id(), sess.id(), "Found sid %s when expecting %s." % (saved_sess.id(), sess.id()))
		self.failUnlessEqual(saved_sess['test_data'], 'test', "Session data was not saved properly.")
	
	def test_messages(self):
		req = self.get_request()
		req['modu.session'] = sess = session.DbUserSession(req, self.store.pool)
		req['modu.messages'] = message.Queue(req)
		
		req.messages.report('error', 'Sample Error')
		req.session.save()
		
		req = self.get_request()
		req['modu.session'] = saved_sess = session.DbUserSession(req, self.store.pool, sid=sess.id())
		req['modu.messages'] = message.Queue(req)
		
		self.failUnlessEqual(saved_sess.id(), sess.id(), "Found sid %s when expecting %s." % (saved_sess.id(), sess.id()))
		self.failUnlessEqual(req.messages.get('error'), ['Sample Error'], "Session data was not saved properly.")
	
	def test_noclobber(self):
		req = self.get_request()
		
		sessid = session.generate_token()
		sess = session.DbUserSession(req, self.store.pool, sessid)
		sess2 = session.DbUserSession(req, self.store.pool, sessid)
		sess['test_data'] = 'something'
		sess.save()
		sess2.save()
		
		saved_sess = session.DbUserSession(req, self.store.pool, sid=sess.id())
		self.failUnlessEqual(saved_sess['test_data'], 'something', "Session data was not saved properly.")
		
		sess.delete()
		sess2.delete()
	
	def test_users(self):
		req = self.get_request()
		
		usr = user.User()
		usr.username = 'sampleuser'
		usr.first = 'Sample'
		usr.last = 'User'
		usr.crypt = RAW("ENCRYPT('%s')" % 'password')
		
		self.store.ensure_factory('user')
		self.store.save(usr)
		
		sess = session.DbUserSession(req, self.store.pool)
		sess.set_user(usr)
		sess.save()
		
		for header, data in req.app.get_headers():
			if(header == 'Set-Cookie'):
				req['HTTP_COOKIE'] = data.strip()
		
		saved_sess = session.DbUserSession(req, self.store.pool)
		saved_user = saved_sess.get_user()
		self.failUnlessEqual(saved_sess._user_id, sess._user_id, "Found user_id %s when expecting %d." % (saved_sess._user_id, sess._user_id))
		self.failUnlessEqual(saved_user.get_id(), usr.get_id(), "User ID changed during save/load cycle.")
		self.failUnlessEqual(saved_user.username, usr.username, "Username changed during save/load cycle.")
		
		self.store.destroy(saved_user)
