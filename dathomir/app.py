# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, mimetypes, os, stat, os.path
from dathomir.util import url
from dathomir import session, persist
from mod_python import apache, util

base_path = '/'
db_url = 'mysql://dathomir:dathomir@localhost/dathomir'
session_class = session.UserSession
initialize_store = True
webroot = 'webroot'
debug_session = False

def activate(rsrc):
	global _site_tree
	for path in rsrc.get_paths():
		_site_tree.register(path, rsrc)

def handler(req):
	req.dathomir = _dathomir_namespace()
	
	global base_path
	if(req.uri.startswith(base_path)):
		req.dathomir.path = req.uri[len(base_path):]
	else:
		req.dathomir.path = req.uri
	
	req.dathomir.approot = apache.get_handler_root()
	
	result = _handle_file(req)
	if(result):
		if(result[1]):
			req.content_type = result[1]
			req.set_content_length(result[2])
			req.sendfile(result[0])
			return apache.OK
		else:
			return apache.HTTP_FORBIDDEN
	else:
		rsrc = _site_tree.parse(req.dathomir.path)
		if not(rsrc):
			return apache.HTTP_NOT_FOUND
		
		req.dathomir.tree = _site_tree
		
		for key, value in _bootstrap(req).iteritems():
			setattr(req.dathomir, key, value)
		
		rsrc.prepare_content(req)
		req.content_type = rsrc.get_content_type(req)
		content = rsrc.get_content(req)
		req.set_content_length(len(content))
		req.write(content)
		
		global db_url, session_class
		if(db_url and session_class):
			req.session.save()
	
	return apache.OK

_site_tree = url.URLNode()
_db = None

class _dathomir_namespace(dict):
	def __getattribute__(self, key):
		if(key in self):
			return self[key]
		raise AttributeError(key)
	
	def __setattr__(self, key, value):
		self[key] = value

def _handle_file(req):
	global webroot
	if(webroot.startswith('/')):
		true_path = webroot
	else:
		true_path = os.path.join(req.dathomir.approot, webroot)
	
	true_path = os.path.join(true_path, req.dathomir.path)
	try:
		finfo = os.stat(true_path)
	
		if(stat.S_ISREG(finfo.st_mode)):
			try:
				content_type = mimetypes.guess_type(true_path)[0]
				size = finfo.st_size
				return (true_path, content_type, size)
			except IOError:
				return (true_path, None, None)
	except OSError:
		pass
	
	return None

def _bootstrap(req):
	result = {}
	
	global db_url
	if(db_url):
		result['db'] = _init_database(req)
	
	global session_class
	if(db_url and session_class):
		result['session'] = _init_session(req, result['db'])
	
	global debug_session
	if(debug_session):
		req.log_error('session contains: ' + str(result['session']))
	
	global initialize_store
	if(db_url and initialize_store):
		result['store'] = _init_store(req, result['db'])
	
	return result

def _init_database(req):
	global db_url, _db
	
	if(_db):
		return _db
	
	dsn = url.urlparse(db_url)
	if(dsn['scheme'] == 'mysql'):
		_db = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
	else:
		raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
	
	return _db

def _init_store(req, db):
	store = persist.get_store()
	if not(store):
		store = persist.Store(db)
	return store

def _init_session(req, db):
	sess = session.UserSession(req, db)
	return sess