# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir import persist
from dathomir.persist import storable, interp

from mod_python import Session, apache
from MySQLdb import cursors
import cPickle, time

"""
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

class DbSession(Session.BaseSession):
	def __init__(self, req, connection, sid=None, secret=None, lock=0, timeout=0):
		self.connection = connection
		Session.BaseSession.__init__(self, req, sid, secret, lock, timeout)
	
	def do_cleanup(self):
		self._req.register_cleanup(self.db_cleanup)
		self._req.log_error("DbSession: registered database cleanup.", apache.APLOG_NOTICE)
	
	def do_load(self):
		cur = self.connection.cursor(cursors.SSDictCursor)
		cur.execute("SELECT s.* FROM session s WHERE id = %s", [self.id()])
		record = cur.fetchone()
		if(record):
			result = {'_created':record['created'], '_accessed':record['accessed'], '_timeout':record['timeout']}
			result['_data'] = cPickle.loads(record['data'].tostring())
			self.user_id = record['user_id']
			return result
		else:
			return None
	
	def do_save(self, dict):
		cur = self.connection.cursor()
		if not(hasattr(self, 'user_id') and self.user_id):
			self.user_id = 0
		cur.execute("REPLACE INTO session (id, user_id, created, accessed, timeout, data) VALUES (%s, %s, %s, %s, %s, %s)",
						[self.id(), self.user_id, dict['_created'], dict['_accessed'], dict['_timeout'], cPickle.dumps(dict['_data'], 1)])
	
	def do_delete(self):
		cur = self.connection.cursor()
		cur.execute("DELETE FROM session s WHERE s.id = %s", [self.id()])
	
	def db_cleanup(self, *args):
		self._req.log_error('db_cleanup passed extra args: ' + str(args))
		cur = self.connection.cursor()
		cur.execute("DELETE FROM session s WHERE %s - s.accessed > s.timeout", [int(time.time())])
	
	def get_user(self):
		raise NotImplementedError('%s::get_user()' % self.__class__.__name__)
	
	def set_user(self):
		raise NotImplementedError('%s::set_user()' % self.__class__.__name__)


class User(storable.Storable):
	def __init__(self):
		storable.Storable.__init__(self, 'user')


class UserSession(DbSession):
	user_class = User
	
	def get_user(self):
		if(hasattr(self, 'user') and self.user):
			return self.user
		
		if(hasattr(self, 'user_id') and self.user_id):
			store = persist.get_store()
			if not(store.has_factory('user')):
				store.ensure_factory('user', user_class)
			self.user = store.load_once('user', {'id':self.user_id})
			return self.user
		
		return None
	
	def set_user(self, user):
		self.user = user
		if(self.user):
			self.user_id = self.user.get_id(True)
