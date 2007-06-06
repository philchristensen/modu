# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, mimetypes, os.path
from dathomir.util import url
from dathomir import session, persist
from mod_python import apache, util

base_path = '/'
db_url = 'mysql://dathomir:dathomir@localhost/dathomir'
session_class = session.UserSession
initialize_store = True
webroot = 'webroot'

_site_tree = url.URLNode()
_forbidden_paths = ['DathomirConfig.py']
_db = None

def activate(rsrc):
	global _site_tree
	for path in rsrc.get_paths():
		_site_tree.register(path, rsrc)

def handler(req):
	global base_path	
	if(req.uri.startswith(base_path)):
		req.dathomir_path = req.uri[len(base_path):]
	else:
		req.dathomir_path = req.uri
	
	req.approot = apache.get_handler_root()
	
	result = _handle_file(req)
	if(result is not None):
		return result
	
	rsrc = _site_tree.parse(req.dathomir_path)
	if not(rsrc):
		return apache.HTTP_NOT_FOUND
	
	req.tree = _site_tree
	
	global db_url
	if(db_url):
		req.db = _init_database(req)
	
	global session_class
	if(db_url and session_class):
		req.session = _init_session(req, req.db)
	
	req.log_error('session contains: ' + str(req.session))
	
	global initialize_store
	if(db_url and initialize_store):
		req.store = _init_store(req, req.db)
	
	rsrc.prepare_content(req)
	req.content_type = rsrc.get_content_type(req)
	content = rsrc.get_content(req)
	req.set_content_length(len(content))
	req.write(content)
	
	if(db_url and session_class):
		req.session.save()

	return apache.OK

def _handle_file(req):
	global webroot
	if(webroot.startswith('/')):
		true_path = webroot
	else:
		true_path = os.path.join(req.approot, webroot)
	
	true_path += req.dathomir_path
	req.finfo = apache.stat(true_path, apache.APR_FINFO_MIN)
	
	if(req.finfo.filetype == apache.APR_REG):
		try:
			content_type = mimetypes.guess_type(req.finfo.fname)[0]
			if(content_type):
				req.content_type = content_type
			else:
				return apache.HTTP_INTERNAL_SERVER_ERROR
			
			req.set_content_length(req.finfo.size)
			
			req.sendfile(req.finfo.fname)
		except IOError:
			return apache.HTTP_FORBIDDEN
		else:
			return apache.OK
		
	return None

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