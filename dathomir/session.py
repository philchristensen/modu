# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import Cookie, time, re, random
from dathomir.persist import storable
from MySQLdb import cursors

import cPickle

"""
The change to WSGI support meant I needed to find a substitute for
mod_python.util.Session. I mimicked a great deal of the original
class, but I did omit some things.

The biggest omission was locking. Since I only wanted a DB-based
session, I let the DB take care of locking operations, which would
be a problem for non threadsafe session storage.

Other changes or omissions are outlined below.
"""

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

VALIDATE_SID_RE = re.compile('[0-9a-f]{32}$')
CLEANUP_CHANCE = 1000

def generate_token(entropy=None):
	"""
	This function is used to generate "unique" session IDs. It's
	not nearly as fancy as it probably should be.
	"""
	try:
		import hashlib
	except:
		import md5 as hashlib
	if not(entropy):
		entropy = random.randint(0, 1)
	
	return hashlib.md5(str(time.time() * entropy)).hexdigest()

def validate_sid(sid):
	"""
	For file-based sessions this is really important, but not so
	much for DB ones, since we're already pretty careful about
	escaping SQL.
	
	File based-sessions could potentially be exploited by using
	slashes and .. to access non-session data.
	"""
	return VALIDATE_SID_RE.match(sid)

class BaseSession(dict):
	"""
	BaseSession should never be instantiated. It's an abstract class
	that takes care of session ID creation and cookie management,
	while delegating actual storage tasks to subclasses.
	
	This is where locking should be implemented, one day.
	"""
	def __init__(self, req, sid=None):
		self._req = req
		self._cookie = None
		self._valid = True
		
		self._sid = None
		self._created = time.time()
		self._accessed = time.time()
		self._timeout = 1800
		
		if(sid and validate_sid(sid)):
			self._sid = sid
		else:
			self._cookie = Cookie.SimpleCookie(req.setdefault('HTTP_COOKIE', ''))
			if('sid' in self._cookie and validate_sid(self._cookie['sid'].value)):
				self._sid = self._cookie['sid'].value
			else:
				self._cookie = Cookie.SimpleCookie()
				self._sid = generate_token()
				self._cookie['sid'] = self._sid
				self._send_cookie()
		
		if(self._sid):
			self.load()
		
		if(random.randint(1, CLEANUP_CHANCE) == 1):
			self.cleanup()
	
	def _send_cookie(self):
		"""
		Add the proper cookie-setting headers to the output.
		"""
		from dathomir import app
		
		cookie_data = self._cookie.output()
		for header in cookie_data.split("\n"):
			header, data = header.split(":")
			app.add_header(header, data)
	
	def invalidate(self):
		self._cookie['sid']['expires'] = 0
		self._send_cookie()
		self.delete()
		self._valid = False
	
	def load(self):
		result = self.do_load()
		if result is None:
			return False
		
		if (time.time() - result["_accessed"]) > result["_timeout"]:
			return False
		
		self._created  = result["_created"]
		self._accessed = result["_accessed"]
		self._timeout  = result["_timeout"]
		self.update(result["_data"])
		return True
	
	def save(self):
		if self._valid:
			result = {"_data"	   : self.copy(), 
					"_created" : self._created, 
					"_accessed": self._accessed, 
					"_timeout" : self._timeout}
			self.do_save(result)
	
	def delete(self):
		self.do_delete()
		self.clear()
	
	def id(self):
		return self._sid
	
	def created(self):
		return self._created
	
	def last_accessed(self):
		return self._accessed
	
	def timeout(self):
		return self._timeout
	
	def set_timeout(self, secs):
		self._timeout = secs
	
	def cleanup(self):
		self.do_cleanup()


class DbSession(BaseSession):
	def __init__(self, req, connection, sid=None):
		self._connection = connection
		BaseSession.__init__(self, req, sid)
	
	def do_load(self):
		cur = self._connection.cursor(cursors.SSDictCursor)
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
		cur = self._connection.cursor()
		if not(hasattr(self, 'user_id') and self.user_id):
			self.user_id = 0
		cur.execute("REPLACE INTO session (id, user_id, created, accessed, timeout, data) VALUES (%s, %s, %s, %s, %s, %s)",
						[self.id(), self.user_id, dict['_created'], dict['_accessed'], dict['_timeout'], cPickle.dumps(dict['_data'], 1)])
	
	def do_delete(self):
		cur = self._connection.cursor()
		cur.execute("DELETE FROM session s WHERE s.id = %s", [self.id()])
	
	def do_cleanup(self, *args):
		self._req.log_error('db_cleanup passed extra args: ' + str(args))
		cur = self._connection.cursor()
		cur.execute("DELETE FROM session s WHERE %s - s.accessed > s.timeout", [int(time.time())])
	
	def get_user(self):
		raise NotImplementedError('%s::get_user()' % self.__class__.__name__)
	
	def set_user(self):
		raise NotImplementedError('%s::set_user()' % self.__class__.__name__)


class User(storable.Storable):
	def __init__(self):
		super(User, self).__init__('user')


class UserSession(DbSession):
	"""
	This is broken. It's a dict, shouldn't be using attribute access.
	"""
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
