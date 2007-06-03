# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb
from dathomir.util import url
from dathomir import session, persist
from mod_python import apache

_site_tree = url.URLNode()
_db = None

base_path = '/'
db_url = 'mysql://dathomir:dathomir@localhost/dathomir'
session_class = session.UserSession
initialize_store = True

def activate(rsrc):
	global _site_tree
	for path in rsrc.get_paths():
		_site_tree.register(path, rsrc)

def handler(req):
	global base_path, session_class, initialize_store, db_url
	
	if(req.uri.startswith(base_path)):
		req.dathomir_path = req.uri[len(base_path):]
	else:
		req.dathomir_path = req.uri
	
	rsrc = _site_tree.parse(req.dathomir_path)
	if not(rsrc):
		return apache.HTTP_NOT_FOUND
	
	req.approot = apache.get_handler_root()
	
	if(db_url):
		req.db = init_database(req)
	
	if(db_url and session_class):
		req.session = init_session(req, req.db)
	
	if(db_url and initialize_store):
		req.store = init_store(req, req.db)
	
	rsrc.prepare_content(req)
	req.content_type = rsrc.get_content_type(req)
	content = rsrc.get_content(req)
	req.set_content_length(len(content))
	req.write(content)
	
	return apache.OK

def init_database(req):
	global db_url, _db
	
	dsn = url.urlparse(db_url)
	
	if(dsn['scheme'] == 'mysql'):
		_db = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
	else:
		raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
	
	return _db

def init_store(req, db):
	store = persist.get_store()
	if not(store):
		store = persist.Store(db)
	return store

def init_session(req, db):
	sess = session.UserSession(req, db)
	return sess