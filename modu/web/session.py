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
	app = req.app
	
	cookie_params = {}
	if(hasattr(app, 'session_cookie_params')):
		cookie_params.update(app.session_cookie_params)
	
	req['modu.session'] = app.session_class(req, req.pool, cookie_params=cookie_params)
	if(app.debug_session):
		req.log_error('session contains: ' + str(req.session))
	if(app.disable_session_users):
		if(app.enable_anonymous_users):
			req['modu.user'] = user.AnonymousUser()
		else:
			req['modu.user'] = None
	else:
		req['modu.user'] = req.session.get_user()
		if(req.user is None and app.enable_anonymous_users):
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
	def __init__(self, req, sid=None, cookie_params=None):
		self._req = req
		if(isinstance(cookie_params, dict)):
			self._cookie_params = cookie_params
		else:
			self._cookie_params = {}
		
		self._sid = None
		self._cookie = None
		self._valid = True
		self._clean = True
		self._new = True
		self._loaded = False
		self._user = None
		self._user_id = None
		
		self._created = time.time()
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
				for k, v in self._cookie_params.items():
					self._cookie['sid'][k] = v
				self._send_cookie()
		
		if(self._sid):
			if(self.load()):
				self._new = False
		
		self._accessed = time.time()
		
		if(req.app.debug_session):
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
			self._req.app.add_header(header, data)
	
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
		
		if (time.time() - result["accessed"]) > result["timeout"]:
			self.delete()
			return False
		
		self._created  = result["created"]
		self._accessed = result["accessed"]
		self._timeout  = result["timeout"]
		self._user_id = result.get("user_id", None)
		if(result["data"]):
			self.update(result["data"])
		return True
	
	def save(self):
		"""
		Save the session data for this object's session ID
		"""
		if self._valid:
			result = {"data" : self.copy(), 
					"created" : self._created, 
					"accessed": self._accessed, 
					"timeout" : self._timeout,
					"user_id" : self._user_id}
			if(self._req.app.debug_session):
				self._req.log_error('session cleanliness is: ' + str(self.is_clean()))
			self.do_save(result)
			self._new = False
	
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
	
	def is_new(self):
		return self._new
	
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
	
	def __init__(self, req, pool, sid=None, cookie_params=None):
		self._pool = pool
		BaseSession.__init__(self, req, sid=sid, cookie_params=cookie_params)
	
	def do_load(self):
		load_query = persist.build_select('session', {'id':self.id()})
		record = self._pool.runQuery(load_query)
		
		if(record):
			record = record[0]
			record['id'] = self.id()
			if(record['data']):
				record['data'] = cPickle.loads(record['data'].tostring())
			else:
				record['data'] = None
			return record
		else:
			return None
	
	def do_save(self, attribs):
		if(self.is_clean() or not self.is_new()):
			del attribs['data']
			update_query = persist.build_update('session', attribs, {'id':self.id()})
			self._pool.runOperation(update_query)
		else:
			attribs['id'] = self.id()
			attribs['data'] = cPickle.dumps(attribs['data'], 1)
			insert_query = persist.build_insert('session', attribs)
			self._pool.runOperation(insert_query)
	
	def do_delete(self):
		self._pool.runOperation("DELETE FROM session WHERE id = %s", [self.id()])
	
	def do_cleanup(self, *args):
		self._pool.runOperation("DELETE FROM session WHERE timeout < (%s - accessed)", [int(time.time())])
	
	def get_user(self):
		if(hasattr(self, '_user') and self._user):
			return self._user
		
		if(self._user_id is not None):
			store = self._req.store
			if not(store.has_factory('user')):
				store.ensure_factory('user', self.user_class)
			self._user = store.load_one('user', {'id':self._user_id})
		
		return self._user
	
	def set_user(self, u):
		self.touch()
		self._user = u
		self._req['modu.user'] = u
		if(self._user):
			self._user_id = self._user.get_id()
		else:
			self._user_id = None
		
		if(u is None and self._req.app.enable_anonymous_users):
			self._user = user.AnonymousUser()

