# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import url
from modu.web import session, wsgi
from modu import persist

base_url = '/'
db_url = 'mysql://modu:modu@localhost/modu'
session_class = session.UserSession
initialize_store = True
default_guid_table = 'guid'
webroot = 'webroot'
debug_session = False
debug_store = False

_site_tree = url.URLNode()
_db = None
_response_headers = []

def activate(rsrc):
	"""
	Add a resource to this site's URLNode tree
	"""
	global _site_tree
	for path in rsrc.get_paths():
		_site_tree.register(path, rsrc)

def get_tree():
	"""
	Return this site's URLNode tree
	"""
	global _site_tree
	return _site_tree

def add_header(header, data):
	"""
	Store headers for later retrieval.
	"""
	global _response_headers
	_response_headers.append((header, data))

def has_header(header):
	"""
	Check if a header has ever been set.
	"""
	global _response_headers
	for h, d in _response_headers:
		if(h == header):
			return True
	return False

def get_headers():
	"""
	Get accumulated headers
	"""
	global _response_headers
	return _response_headers

def load_config(req):
	"""
	Load this app's configuration variables into the
	provided request object.
	"""
	global db_url, session_class, initialize_store
	global base_url, webroot, debug_store, debug_session
	
	req['modu.config.db_url'] = db_url
	req['modu.config.session_class'] = session_class
	req['modu.config.initialize_store'] = initialize_store
	req['modu.config.base_url'] = base_url
	req['modu.config.webroot'] = webroot
	
	req['modu.config.debug_session'] = debug_session
	req['modu.config.debug_store'] = debug_store

def bootstrap(req):
	"""
	Initialize the common services, store them in the
	provided request variable.
	"""
	# Databases are a slightly special case. Since we want to re-use
	# db connections as much as possible, we keep the current connection
	# as a global variable. Ordinarily this is a naughty-no-no in mod_python,
	# but we're going to be very very careful.
	global _db
	db_url = req['modu.config.db_url']
	if(not _db and db_url):
		dsn = url.urlparse(req['modu.config.db_url'])
		if(dsn['scheme'] == 'mysql'):
			import MySQLdb
			_db = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
		else:
			raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
	req['modu.db'] = _db
	
	# FIXME: We assume that any session class requires database access, and pass
	# the db connection as the second paramter to the session class constructor
	session_class = req['modu.config.session_class']
	if(db_url and session_class):
		req['modu.session'] = session_class(req, req['modu.db'])
		if(req['modu.config.debug_session']):
			req.log_error('session contains: ' + str(req['modu.session']))
	
	initialize_store = req['modu.config.initialize_store']
	if(_db):
		# FIXME: I really can't think of any scenario where a store will
		# already be initialized, but we'll check anyway, for now
		store = persist.get_store()
		if not(store):
			if(req['modu.config.debug_store']):
				debug_file = req['wsgi.errors']
			else:
				debug_file = None
			global default_guid_table
			store = persist.Store(_db, guid_table=default_guid_table, debug_file=debug_file)
		req['modu.store'] = store
