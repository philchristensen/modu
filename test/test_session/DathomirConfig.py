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
from dathomir import config, resource, persist, session

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
		cur = self.req.db.cursor()
		cur.execute(TEST_TABLES)
	
	def tearDown(self):
		pass
	
	def test_create(self):
		self.req.log_error('creating session object')
		sess = session.DbSession(self.req, self.req.db)
		self.req.log_error('updating session object')
		sess['test_data'] = 'test'
		self.req.log_error('saving session object')
		sess.save()
		
		self.req.log_error('loading session object with sess id: ' + sess.id())
		saved_sess = session.DbSession(self.req, self.req.db, sid=sess.id())
		self.req.log_error('comparing session object')
		self.failUnlessEqual(saved_sess['test_data'], 'test', "Session data was not saved properly.")
	
class SessionTestResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		stream = cStringIO.StringIO()
		runner = unittest.TextTestRunner(stream=stream, descriptions=1, verbosity=1)
		loader = unittest.TestLoader()
		DbSessionTestCase.req = req
		test = loader.loadTestsFromTestCase(DbSessionTestCase)
		runner.run(test)
		self.add_slot('content', stream.getvalue())
		stream.close()
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl' 

config.base_path = '/dathomir/test/test_session'
config.session_class = None
config.activate(SessionTestResource())
