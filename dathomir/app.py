# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb
from dathomir.util import url
from dathomir import session, persist, wsgi
from mod_python import apache

base_url = '/'
db_url = 'mysql://dathomir:dathomir@localhost/dathomir'
session_class = session.UserSession
initialize_store = True
webroot = 'webroot'
debug_session = False

_site_tree = url.URLNode()
_db = None
_response_headers = []

def handler(mp_req):
	"""
	The ModPython handler. This will create the necessary
	environment dictionary, and hand off to the WSGI handler.
	"""
	req = wsgi.get_environment(mp_req)
	
	def start_response(status, response_headers):
		mp_req.status = int(status[:3])
		
		for key, val in response_headers:
			if key.lower() == 'content-length':
				mp_req.set_content_length(long(val))
			elif key.lower() == 'content-type':
				mp_req.content_type = val
			else:
				mp_req.headers_out.add(key, val)
		
		return mp_req.write
	
	content = wsgi.handler(req, start_response)
	if(isinstance(content, wsgi.FileWrapper)):
		mp_req.sendfile(content.filelike.name)
	else:
		for data in content:
			mp_req.write(data)
	return apache.OK

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
	return _site_tree

def add_header(header, data):
	global _response_headers
	_response_headers.append((header, data))

def get_headers():
	return _response_headers

def load_config(req):
	req['dathomir.config.db_url'] = db_url
	req['dathomir.config.session_class'] = session_class
	req['dathomir.config.debug_session'] = debug_session
	req['dathomir.config.initialize_store'] = initialize_store
	req['dathomir.config.base_url'] = base_url
	req['dathomir.config.webroot'] = webroot

def bootstrap(req):
	global _db
	db_url = req['dathomir.config.db_url']
	if(not _db and db_url):
		dsn = url.urlparse(req['dathomir.config.db_url'])
		if(dsn['scheme'] == 'mysql'):
			_db = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
		else:
			raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
	req['dathomir.db'] = _db
	
	session_class = req['dathomir.config.session_class']
	if(db_url and session_class):
		req['dathomir.session'] = session.UserSession(req, req['dathomir.db'])
	
	if(req['dathomir.config.debug_session']):
		req.log_error('session contains: ' + str(result['dathomir.session']))
	
	initialize_store = req['dathomir.config.initialize_store']
	if(db_url and initialize_store):
		store = persist.get_store()
		if not(store):
			store = persist.Store(db)
		req['dathomir.store'] = store
