# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os, os.path, sys, stat, copy, mimetypes, traceback, threading

from modu.util import url, tags, queue
from modu.web import session, user, resource, static
from modu import persist, web

from twisted import plugin
from twisted.python import log
from zope import interface

host_tree = {}
host_tree_lock = threading.BoundedSemaphore()

pool = None
pool_lock = threading.BoundedSemaphore()

mimetypes_init = False

def handler(env, start_response):
	req = {}
	try:
		try:
			application = get_application(env)
			
			if(application):
				req = configure_request(env, application)
			else:
				raise404("No such application: %s" % env['REQUEST_URI'])
			
			if(req.app.db_url):
				req.set_jit('modu.pool', activate_pool)
			if(req.app.db_url and application.initialize_store):
				req.set_jit('modu.store', persist.activate_store)
			if(req.app.db_url and req.app.session_class):
				req.set_jit('modu.session', session.activate_session)
				req.set_jit('modu.user', session.activate_session)
			if not(req.app.disable_message_queue):
				req.set_jit('modu.messages', queue.activate_messages)
			
			req.set_jit('modu.content', queue.activate_content_queue)
			
			if(hasattr(application.site, 'configure_request')):
				application.site.configure_request(req)
			rsrc = req.app.tree.parse(req.path)
			
			if not(rsrc):
				raise404("No such resource: %s" % env['REQUEST_URI'])
			
			if(resource.IResourceDelegate.providedBy(rsrc)):
				rsrc = rsrc.get_delegate(req)
			if(resource.IAccessControl.providedBy(rsrc)):
				rsrc.check_access(req)
			
			content = rsrc.get_response(req)
		finally:
			# remember, req.get will return None if the session wasn't used
			# in this page load
			if(req.get('modu.session', None) is not None):
				req.session.save()
	except web.HTTPStatus, http:
		start_response(http.status, http.headers)
		return http.content
	
	start_response('200 OK', application.get_headers())
	return content


def configure_request(env, application):
	env['modu.app'] = application
	
	env['SCRIPT_NAME'] = application.base_path
	
	# once the previous line is gone, this next
	# block should be able to be moved elsewhere
	if(env['REQUEST_URI'].find('?') < 0):
		uri = env['REQUEST_URI']
	else:
		# twisted.web2.wsgi includes the query string in the request_uri
		uri, qs = env['REQUEST_URI'].split('?')
	
	if(uri.startswith(env['SCRIPT_NAME'])):
		env['PATH_INFO'] = uri[len(env['SCRIPT_NAME']):]
	else:
		env['PATH_INFO'] = uri
	
	env['modu.approot'] = env['SCRIPT_FILENAME']
	env['modu.path'] = env['PATH_INFO']
	
	approot = env['modu.approot']
	webroot = os.path.join(approot, application.webroot)
	env['PATH_TRANSLATED'] = os.path.realpath(webroot + env['modu.path'])
	
	return Request(env)


def get_application(req):
	"""
	Return an application object for the site configured
	at the path specified in req.
	
	Note that ISite plugins are only searched when the
	specified host/path is not found.
	"""
	global host_tree
	
	host = req.get('HTTP_HOST', req['SERVER_NAME'])
	if(host.find(':') == -1):
		host += ':' + req['SERVER_PORT']
	
	host_tree_lock.acquire()
	try:
		if not(host in host_tree):
			_scan_sites(req)
		if not(host in host_tree):
			return None
		
		host_node = host_tree[host]
		
		if not(host_node.has_path(req['REQUEST_URI'])):
			_scan_sites(req)
		
		app = host_node.get_data_at(req['REQUEST_URI'])
	finally:
		host_tree_lock.release()
	
	return copy.deepcopy(app)


def redirect(url, permanent=False):
	"""
	Because I want to, that's why.
	"""
	if(permanent):
		raise301(url)
	else:
		raise302(url)


def raise200(headers, content):
	raise web.HTTPStatus('200 OK', headers, content)


def raise301(url):
	raise web.HTTPStatus('301 Moved Permanently', [('Location', url)], [''])


def raise302(url):
	raise web.HTTPStatus('302 Found', [('Location', url)], [''])


def raise404(path=None):
	content = tags.h1()['Not Found']
	content += tags.hr()
	content += tags.p()['There is no object registered at that path.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('404 Not Found', [('Content-Type', 'text/html')], [content])


def raise403(path=None):
	content = tags.h1()['Forbidden']
	content += tags.hr()
	content += tags.p()['You are not allowed to access that path.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('403 Forbidden', [('Content-Type', 'text/html')], [content])


def raise401(path=None):
	content = tags.h1()['Unauthorized']
	content += tags.hr()
	content += tags.p()['You have not supplied the appropriate credentials.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('401 Unauthorized', [('Content-Type', 'text/html')], [content])


def raise500(message=None):
	content = tags.h1()['Internal Server Error']
	content += tags.hr()
	content += tags.p()['Sorry, an error has occurred:']
	if(message):
		content += tags.strong()[message]
	raise web.HTTPStatus('500 Internal Server Error', [('Content-Type', 'text/html')], content)


def activate_pool(req):
	req['modu.pool'] = acquire_db(req.app.db_url)


def acquire_db(db_url):
	global pool, pool_lock
	pool_lock.acquire()
	try:
		if not(pool):
			from modu.persist import adbapi
			pool = adbapi.connect(db_url)
	finally:
		pool_lock.release()
	
	return pool


def _scan_sites(env):
	global host_tree
	
	if(env.get('SCRIPT_FILENAME', sys.path[0]) not in sys.path):
		sys.path.append(env['SCRIPT_FILENAME'])
	
	import modu.sites
	reload(modu.sites)
	
	for site_plugin in plugin.getPlugins(ISite, modu.sites):
		site = site_plugin()
		app = Application(site)
		
		# We can't set up the default file resource if we
		# don't know where we are
		if('SCRIPT_FILENAME' in env):
			root = app.tree.get_data_at('/')
			webroot = os.path.join(env['SCRIPT_FILENAME'], app.webroot)
			file_root = static.FileResource(['/'], webroot, root)
			app.tree.register('/', file_root, clobber=True)
		
		domain = app.base_domain
		if(domain.find(':') == -1):
			domain += ':' + env['SERVER_PORT']
		
		host_node = host_tree.setdefault(domain, url.URLNode())
		base_path = app.base_path
		if not(base_path):
			base_path = '/'
		host_node.register(base_path, app, clobber=True)


class ISite(interface.Interface):
	"""
	An ISitePlugin defines an application that responds to
	a certain hostname and/or path.
	"""
	def initialize(self, app):
		"""
		Configure the application object for this site. This method is
		only called once for the lifetime of the app object.
		"""


class Request(dict):
	"""
	At this point we are supposedly server-neutral, although
	the code does make a few assumptions about what various
	environment variables actually mean. Shocking.
	"""
	def __init__(self, env={}):
		dict.__init__(self)
		self.update(env)
		self.jit_handlers = {}
	
	def __getattr__(self, key):
		modu_key = 'modu.%s' % key
		if(modu_key in self.jit_handlers or modu_key in self):
			return self[modu_key]
		raise AttributeError(key)
	
	def __getitem__(self, key):
		self.handle_jit(key)
		return dict.__getitem__(self, key)
	
	def __contains__(self, key):
		if(key in self.jit_handlers):
			return True
		return dict.__contains__(self, key)
	
	def handle_jit(self, key):
		if(not dict.__contains__(self, key) and key in self.jit_handlers):
			handler = self.jit_handlers[key]
			#print 'activating %s with %r' % (key, handler)
			handler(self)
	
	def set_jit(self, key, handler):
		self.jit_handlers[key] = handler
	
	def log_error(self, data):
		self['wsgi.errors'].write(data)
	
	def has_form_data(self):
		if(self['REQUEST_METHOD'] == 'POST'):
			return True
		elif(self['QUERY_STRING']):
			return True
		return False
	
	def get_path(self, *args, **options):
		def _deslash(fragment):
			fragment = str(fragment)
			if(fragment.startswith('/')):
				return fragment[1:]
			else:
				return fragment
		
		args = map(_deslash, args)
		result = os.path.join(self.app.base_path, *args)
		if(self.app.base_path == '/' and not args):
			return ''
		
		return result


class Application(object):
	"""
	An 'application' in the modu universe is simply a place
	to store static configuration data about a particular
	hostname and path on a webserver.
	
	When writing ISite plugins, you'll be populating an empty
	instance of this class, which will be cloned and stored
	in the request object for each page request.
	"""
	def __init__(self, site):
		_dict = self.__dict__
		_dict['_response_headers'] = []
		_dict['config'] = {}
		
		self.base_domain = 'localhost'
		self.base_path = '/'
		self.db_url = 'MySQLdb://modu:modu@localhost/modu'
		self.session_class = session.DbUserSession
		self.initialize_store = True
		self.webroot = 'webroot'
		self.debug_session = False
		self.debug_store = False
		self.enable_anonymous_users = True
		self.disable_session_users = False
		self.disable_message_queue = False
		self.magic_mime_file = None
		self.tree = url.URLNode()
		self.site = site
		
		site.initialize(self)
	
	def __setattr__(self, key, value):
		self.config[key] = value
	
	def __getattr__(self, key):
		if(key.startswith('_')):
			return super(Application, self).__getattr__(key)
		return self.__dict__['config'][key]
	
	def activate(self, rsrc):
		"""
		Add a resource to this site's URLNode tree
		"""
		if not resource.IResource.providedBy(rsrc):
			raise TypeError('%r does not implement IResource' % rsrc)
		
		for path in rsrc.get_paths():
			self.tree.register(path, rsrc)
	
	def get_tree(self):
		"""
		Return this site's URLNode tree
		"""
		return self.tree
	
	def add_header(self, header, data):
		"""
		Store headers for later retrieval.
		"""
		self._response_headers.append((header, data))
	
	def has_header(self, header):
		"""
		Check if a header has ever been set.
		"""
		for h, d in self._response_headers:
			if(h == header):
				return True
		return False
	
	def get_headers(self):
		"""
		Get accumulated headers
		"""
		return self._response_headers
