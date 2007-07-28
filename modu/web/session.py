# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import Cookie, time, re, random
from MySQLdb import cursors

import cPickle

from modu.web import user
from modu import persist

"""
The change to WSGI support meant I needed to find a substitute for
mod_python.util.Session. I mimicked a great deal of the original
class, but I did omit some things.

The biggest omission was locking. Since I only wanted a DB-based
session, I let the DB take care of locking operations, which would
be a problem for non threadsafe session storage.

Other changes or omissions are outlined below.
"""

VALIDATE_SID_RE = re.compile('[0-9a-f]{32}$')
CLEANUP_CHANCE = 1000

def activate_session(req):
	# FIXME: We assume that any session class requires database access, and pass
	# the db connection as the second paramter to the session class constructor
	app = req['modu.app']
	session_class = app.session_class
	db_url = app.db_url
	if(db_url and session_class):
		req['modu.session'] = session_class(req, req['modu.db_pool'])
		if(app.debug_session):
			req.log_error('session contains: ' + str(req['modu.session']))
		if(app.disable_session_users):
			if(app.enable_anonymous_users):
				req['modu.user'] = user.AnonymousUser()
			else:
				req['modu.user'] = None
		else:
			req['modu.user'] = req['modu.session'].get_user()
			if(req['modu.user'] is None and app.enable_anonymous_users):
				req['modu.user'] = user.AnonymousUser()

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
		self._clean = True
		self._loaded = False
		
		self._sid = None
		self._created = time.time()
		self._timeout = 1800
		
		self._user = None
		self._user_id = None
		
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
		
		self._accessed = time.time()
		
		if(req['modu.app'].debug_session):
			req.log_error('session contains: ' + str(self))

		if(random.randint(1, CLEANUP_CHANCE) == 1):
			self.cleanup()
		
		self._loaded = True
	
	def touch(self):
		"""
		Mark this session as dirty.
		"""
		self._clean = False
	
	def _send_cookie(self):
		"""
		Add the proper cookie-setting headers to the output.
		"""
		cookie_data = self._cookie.output()
		for header in cookie_data.split("\n"):
			header, data = header.split(":")
			self._req['modu.app'].add_header(header, data)
	
	def invalidate(self):
		"""
		Delete and dishonor this session.
		"""
		self._cookie['sid']['expires'] = 0
		self._send_cookie()
		self.delete()
		self._valid = False
	
	def load(self):
		"""
		Load the session data for this object's session ID
		"""
		result = self.do_load()
		if result is None:
			return False
		
		if (time.time() - result["_accessed"]) > result["_timeout"]:
			return False
		
		self._created  = result["_created"]
		self._accessed = result["_accessed"]
		self._timeout  = result["_timeout"]
		self._user_id = result.get("_user_id", None)
		if(result["_data"]):
			self.update(result["_data"])
		return True
	
	def save(self):
		"""
		Save the session data for this object's session ID
		"""
		if self._valid:
			result = {"_data"	   : self.copy(), 
					"_created" : self._created, 
					"_accessed": self._accessed, 
					"_timeout" : self._timeout,
					"_user_id" : self._user_id}
			if(self._req['modu.app'].debug_session):
				self._req.log_error('session cleanliness is: ' + str(self.is_clean()))
			self.do_save(result)
	
	def delete(self):
		"""
		Delete this session's record from the DB
		"""
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
	
	def is_clean(self):
		return self._clean
	
	def __setitem__(self, key, value):
		if(self._loaded):
			self.touch()
		dict.__setitem__(self, key, value)
	
	def __delitem__(self, key):
		if(self._loaded):
			self.touch()
		dict.__delitem__(self, key)
	
	def setdefault(self, key, value=None):
		if(self._loaded):
			self.touch()
		return dict.setdefault(self, key, value)
	
	def clear(self):
		if(self._loaded):
			self.touch()
		dict.clear(self)
	
	def update(self, d=None, **kwargs):
		if(self._loaded):
			self.touch()
		dict.update(self, d, **kwargs)
	
	def pop(self, key=None):
		if(self._loaded):
			self.touch()
		dict.pop(self, key)
	
	def popitem(self):
		if(self._loaded):
			self.touch()
		dict.popitem(self)
	
	def get_user(self):
		raise NotImplementedError('%s::get_user()' % self.__class__.__name__)
	
	def set_user(self):
		raise NotImplementedError('%s::set_user()' % self.__class__.__name__)
	
	def do_load(self):
		raise NotImplementedError('%s::do_load()' % self.__class__.__name__)
	
	def do_save(self):
		raise NotImplementedError('%s::do_save()' % self.__class__.__name__)
	
	def do_delete(self):
		raise NotImplementedError('%s::do_delete()' % self.__class__.__name__)
	
	def do_cleanup(self):
		raise NotImplementedError('%s::do_cleanup()' % self.__class__.__name__)

class DbUserSession(BaseSession):
	"""
	The standard implementor of the BaseSession object.
	"""
	user_class = user.User
	
	def __init__(self, req, connection, sid=None):
		self._connection = connection
		BaseSession.__init__(self, req, sid)
	
	def do_load(self):
		cur = self._connection #.cursor(cursors.SSDictCursor)
		try:
			record = cur.runQuery("SELECT s.* FROM session s WHERE id = %s", [self.id()])
			#record = cur.fetchone()
			if(record):
				result = {'_created':record['created'], '_accessed':record['accessed'],
						  '_timeout':record['timeout'], '_user_id':record['user_id']}
				if(record['data']):
					result['_data'] = cPickle.loads(record['data'].tostring())
				else:
					result['_data'] = None
				return result
			else:
				return None
		finally:
			#cur.fetchall()
			#cur.close()
			pass
	
	def do_save(self, dict):
		cur = self._connection #.cursor()
		try:
			if(self.is_clean()):
				cur.runOperation("UPDATE session s SET s.user_id = %s, s.created = %s, s.accessed = %s, s.timeout = %s WHERE s.id = %s",
							[self._user_id, dict['_created'], dict['_accessed'], dict['_timeout'], self.id()])
			else:
				cur.runOperation("REPLACE INTO session (id, user_id, created, accessed, timeout, data) VALUES (%s, %s, %s, %s, %s, %s)",
							[self.id(), self._user_id, dict['_created'], dict['_accessed'], dict['_timeout'], cPickle.dumps(dict['_data'], 1)])
		finally:
			#cur.fetchall()
			#cur.close()
			pass
	
	def do_delete(self):
		try:
			cur = self._connection #.cursor()
			cur.runOperation("DELETE FROM session WHERE id = %s", [self.id()])
		finally:
			#cur.fetchall()
			#cur.close()
			pass
	
	def do_cleanup(self, *args):
		try:
			cur = self._connection #.cursor()
			cur.runOperation("DELETE FROM session WHERE timeout < (%s - accessed)", [int(time.time())])
		finally:
			#cur.fetchall()
			#cur.close()
			pass
	
	def get_user(self):
		if(hasattr(self, '_user') and self._user):
			return self._user
		
		if(self._user_id is not None):
			store = self._req['modu.store']
			if not(store.has_factory('user')):
				store.ensure_factory('user', self.user_class)
			self._user = store.load_one('user', {'id':self._user_id})
		
		return self._user
	
	def set_user(self, user):
		self._user = user
		if(self._user):
			self._user_id = self._user.get_id()
		else:
			self._user_id = None

