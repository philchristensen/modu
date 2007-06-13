# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, mimetypes, os, stat, os.path
from dathomir.util import url
from dathomir import session, persist, wsgi
from mod_python import apache, util

base_url = '/'
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
	environ = wsgi.get_environment(req)
	environ.update(_get_config_dict())
	
	def start_response(status, response_headers):
		req.status = int(status[:3])
		
		for key, val in response_headers:
			if key.lower() == 'content-length':
				req.set_content_length(int(val))
			elif key.lower() == 'content-type':
				req.content_type = val
			else:
				req.headers_out.add(key, val)
		
		return req.write
	
	content = wsgi_handler(environ, start_response)
	if(isinstance(content, wsgi.FileWrapper)):
		req.sendfile(content.filelike.name, content.blksize)
	else:
		for data in content:
			req.write(data)
	return apache.OK

def wsgi_handler(environ, start_response):
	environ = _req_wrapper(environ)
	
	global base_url
	uri = environ['REQUEST_URI']
	if(uri.startswith(base_url)):
		environ['dathomir.path'] = uri[len(base_url):]
	else:
		environ['dathomir.path'] = uri
	
	# TODO: Fix this
	environ['dathomir.approot'] = apache.get_handler_root()
	
	result = _handle_file(environ)
	if(result):
		content = []
		if(result[1]):
			add_header('Content-Type', result[1])
			add_header('Content-Length', result[2])
			try:
				content = wsgi.FileWrapperopen(open(result[0]))
			except:
				status = '401 Forbidden'
			else:
				status = '200 OK'
		else:
			status = '401 Forbidden'
		start_response(status, get_headers())
		return content
	
	rsrc = _site_tree.parse(environ['dathomir.path'])
	if not(rsrc):
		start_response('404 Not Found', [])
		return []
	
	environ['dathomir.tree'] = _site_tree
	
	for key, value in _bootstrap(environ).iteritems():
		environ['dathomir.' + key] = value
	
	rsrc.prepare_content(environ)
	add_header('Content-Type', rsrc.get_content_type(environ))
	content = rsrc.get_content(environ)
	add_header('Content-Length', len(content))
	
	global db_url, session_class
	if(db_url and session_class):
		environ['dathomir.session'].save()
	
	start_response('200 OK', get_headers())
	return [content]

def add_header(header, data):
	global _response_headers
	_response_headers.append((header, data))

def get_headers():
	return _response_headers

_site_tree = url.URLNode()
_db = None
_response_headers = []

class _req_wrapper(dict):
	def __init__(self, d):
		dict.__init__(self)
		self.update(d)
	
	def log_error(self, data):
		self['wsgi.errors'].write(data)

def _handle_file(req):
	global webroot
	if(webroot.startswith('/')):
		true_path = webroot
	else:
		true_path = os.path.join(req['dathomir.approot'], webroot)
	
	true_path = os.path.join(true_path, req['dathomir.path'])
	try:
		finfo = os.stat(true_path)
		# note that there's no support for directory indexes,
		# only direct file access
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

def _get_config_dict():
	environ = {}
	environ['dathomir.config.db_url'] = db_url
	environ['dathomir.config.session_class'] = session_class
	environ['dathomir.config.debug_session'] = debug_session
	environ['dathomir.config.initialize_store'] = initialize_store
	environ['dathomir.config.base_url'] = base_url
	environ['dathomir.config.webroot'] = webroot
	return environ

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