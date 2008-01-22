
# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Primary components of the modu webapp foundation.

@var host_tree: domain name to URLNode mappings
@type host_tree: dict

@var host_tree_lock: lock on host_tree during C{app.get_application()}
@type host_tree_lock: threading.BoundedSemaphore

@var pool: pool of synchronous database connections, shared between threads
@type pool: adbapi.SynchronousConnectionPool

@var pool_lock: lock on host_tree during site lookup
@type pool_lock: threading.BoundedSemaphore
"""

import os, os.path, sys, stat, copy, mimetypes, traceback, threading

from modu.util import url, tags, queue
from modu.web import session, user, resource, static
from modu import persist, web

from twisted import plugin
from twisted.web import server
from twisted.python import log, failure
from twisted.web.util import formatFailure
from zope import interface

host_tree = {}
host_tree_lock = threading.BoundedSemaphore()

pools = {}
pools_lock = threading.BoundedSemaphore()

mimetypes_init = False

def handler(env, start_response):
	"""
	The primary WSGI application object.
	"""
	#env['wsgi.errors'].write(str(env) + "\n")
	# just in case an error occurs before the request is created for real
	# this lets the error pages add headers to the request response
	req = Request()
	application = None
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
			rsrc = req.get_resource()
			
			if not(rsrc):
				raise404("No such resource: %s" % env['REQUEST_URI'])
			
			if(resource.IResourceDelegate.providedBy(rsrc)):
				rsrc = rsrc.get_delegate(req)
			if(resource.IAccessControl.providedBy(rsrc)):
				rsrc.check_access(req)
			
			req['modu.resource'] = rsrc
			content = rsrc.get_response(req)
		finally:
			# remember, req.get will return None if the session wasn't used
			# in this page load
			if(req.get('modu.session', None) is not None):
				req.session.save()
	except web.HTTPStatus, http:
		headers = http.headers
		if(application):
			headers += req.get_headers()
		content = http.content
		
		if('modu.app' in req and req.app.config.get('status_content')):
			content_provider = req.app.status_content()
			if(hasattr(content_provider, 'handles_status') and content_provider.handles_status(http)):
				content_provider.prepare_content(req)
				content = [content_provider.get_content(req)]
		
		start_response(http.status, headers)
		return content
	except:
		if('modu.app' in req and req.app.config.get('error_content')):
			content_provider = req.app.error_content()
			content_provider.prepare_content(req)
			content = [content_provider.get_content(req)]
			headers = [('Content-Type', content_provider.get_content_type(req))]
		else:
			reason = failure.Failure()
			log.err(reason)
			content = ["<html><head><title>web.Server Traceback (most recent call last)</title></head>"
				"<body><b>web.Server Traceback (most recent call last):</b>\n\n"
				"%s\n\n</body></html>\n" % formatFailure(reason)]
			headers = [('Content-Type', 'text/html')]
		
		start_response('500 Internal Server Error', headers)
		return content
	
	start_response('200 OK', req.get_headers())
	return content

def configure_request(env, application):
	"""
	Create a Request instance for the current HTTP request.
	
	Given a WSGI environment dict and an Application instance,
	return a Request object that encapsulates this thread's data.
	"""
	if('wsgi.file_wrapper' not in env):
		def _file_wrapper(filelike):
			return iter(lambda: filelike.read(8192), '')
		env['wsgi.file_wrapper'] = _file_wrapper
	
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
	
	env['modu.approot'] = application.approot
	env['modu.path'] = env['PATH_INFO']
	
	approot = env['modu.approot']
	webroot = os.path.join(approot, application.webroot)
	env['PATH_TRANSLATED'] = os.path.realpath(webroot + env['modu.path'])
	
	return Request(env)

def get_default_approot(site):
	parts = site.__class__.__module__.split('.')
	package = __import__('.'.join(parts[:-1]), globals(), locals(), parts[-1], 0)
	mod = getattr(package, parts[-1])
	return os.path.abspath(os.path.dirname(os.path.abspath(mod.__file__)) + '/../..')

def get_normalized_hostname(env):
	host = env.get('HTTP_HOST', env['SERVER_NAME'])
	if(host.find(':') == -1):
		host += ':' + env['SERVER_PORT']
	return host

def get_application(env):
	"""
	Return an application object for the site configured
	at the path specified in env.
	
	Note that ISite plugins are only searched when the
	specified host/path is not found.
	"""
	global host_tree
	
	host = get_normalized_hostname(env)
	
	host_tree_lock.acquire()
	try:
		if not(host_tree):
			_scan_sites(env)
		if not(host in host_tree):
			return None
		
		host_node = host_tree[host]
		
		#if not(host_node.has_path(env['REQUEST_URI'])):
		#	_scan_sites(env)
		
		app = host_node.get_data_at(env['REQUEST_URI'])
	finally:
		host_tree_lock.release()
	
	# we should no longer be mutating the app at any point
	#return copy.deepcopy(app)
	return app

def redirect(url, permanent=False):
	"""
	Convenience method for raise301/raise302.
	
	Because I want to, that's why.
	"""
	if(permanent):
		raise301(url)
	else:
		raise302(url)

def raise200(headers, content):
	"""
	Override the content currently being rendered in the current request.
	"""
	raise web.HTTPStatus('200 OK', headers, content)

def raise301(url):
	"""
	Return a permanent redirect status and content to the user.
	"""
	raise web.HTTPStatus('301 Moved Permanently', [('Location', url)], [''])

def raise302(url):
	"""
	Return a temporary redirect status and content to the user.
	"""
	raise web.HTTPStatus('302 Found', [('Location', url)], [''])

def raise404(path=None):
	"""
	Return a Not Found page to the user, with optional path info.
	"""
	content = tags.h1()['Not Found']
	content += tags.hr()
	content += tags.p()['There is no object registered at that path.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('404 Not Found', [('Content-Type', 'text/html')], [content])

def raise403(path=None):
	"""
	You are not allowed to access that path.
	"""
	content = tags.h1()['Forbidden']
	content += tags.hr()
	content += tags.p()['You are not allowed to access that path.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('403 Forbidden', [('Content-Type', 'text/html')], [content])

def raise401(path=None):
	"""
	You have not supplied the appropriate credentials.
	
	Will cause the client browser to display HTTP username/password dialog.
	"""
	content = tags.h1()['Unauthorized']
	content += tags.hr()
	content += tags.p()['You have not supplied the appropriate credentials.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('401 Unauthorized', [('Content-Type', 'text/html')], [content])

def raise500(message=None):
	"""
	Sorry, an error has occurred.
	"""
	content = tags.h1()['Internal Server Error']
	content += tags.hr()
	content += tags.p()['Sorry, an error has occurred:']
	if(message):
		content += tags.strong()[message]
	raise web.HTTPStatus('500 Internal Server Error', [('Content-Type', 'text/html')], content)

def activate_pool(req):
	"""
	JIT Request handler for enabling DB support.
	"""
	req['modu.pool'] = acquire_db(req.app)

def acquire_db(app):
	"""
	Create the shared connection pool for this process.
	"""
	global pools, pools_lock
	pools_lock.acquire()
	try:
		if(app.db_url in pools):
			pool = pools[app.db_url]
		else:
			from modu.persist import adbapi
			pool = adbapi.connect(app.db_url)
			pools[app.db_url] = pool
	finally:
		pools_lock.release()
	
	return pool

def _scan_sites(env):
	"""
	Search for available site configuration objects.
	
	Register any found objects with the internal structures.
	"""
	global host_tree
	
	modu_path = env.get('MODU_PATH', None)
	
	if(modu_path):
		for component in modu_path.split(':'):
			component = os.path.abspath(component)
			if(component not in sys.path):
				sys.path.append(component)
	
	import modu.sites
	#reload(modu.sites)
	
	plugins = plugin.getPlugins(ISite, modu.sites)
	
	for site_plugin in plugins:
		#env['wsgi.errors'].write(str(site_plugin) + "\n")
		site = site_plugin()
		app = Application(site)
		
		root = app.tree.get_data_at('/')
		webroot = os.path.join(app.approot, app.webroot)
		app.tree.register('/', (static.FileResource, (['/'], webroot, root), {}), clobber=True)
		
		domain = app.base_domain
		if(domain.find(':') == -1):
			domain += ':' + env['SERVER_PORT']
		
		host_node = host_tree.setdefault(domain, url.URLNode())
		base_path = app.base_path
		if not(base_path):
			base_path = '/'
		
		env['wsgi.errors'].write('found site config for %s%s' % (domain, base_path))
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
	A representation of an HTTP request, with some modu-specific features.
	
	At this point we are supposedly server-neutral, although
	the code does make a few assumptions about what various
	environment variables actually mean. Shocking.
	"""
	def __init__(self, env={}):
		"""
		Create a blank Request instance.
		
		The result contains the items of the provided environment dictionary.
		
		User code should call C{app.configure_request()} in normal usage.
		"""
		dict.__init__(self)
		self.update(env)
		self.rsrc = None
		self.jit_handlers = {}
		self.prepath = []
		self.postpath = []
		
		self.response_headers = []
	
	def __getattr__(self, key):
		"""
		Override attribute access for modu.* request variables.
		
		As a convenience, keys with a "modu." prefix can be referred to
		with attribute acces, e.g. C{req.app == req['modu.app']}
		"""
		modu_key = 'modu.%s' % key
		if(modu_key in self.jit_handlers or modu_key in self):
			return self[modu_key]
		raise AttributeError(key)
	
	def __getitem__(self, key):
		"""
		Provide JIT "bootstrapping" of expensive request data.
		
		This allows things like sessions to only be created/loaded
		when actually referred to by application code.
		"""
		self._handle_jit(key)
		return dict.__getitem__(self, key)
	
	def __contains__(self, key):
		"""
		Provide containment info for JIT handled variables.
		
		If a Request instance supports a JIT variable,
		C{'jit_var' in req} will return True. To see if a
		JIT variable has been instantiated or not, use
		C{req.get('jit_var', None) is None}
		"""
		if(key in self.jit_handlers):
			return True
		return dict.__contains__(self, key)
	
	def _handle_jit(self, key):
		"""
		Internal function.
		
		Activate a JIT key if it hasn't been created already.
		"""
		if(not dict.__contains__(self, key) and key in self.jit_handlers):
			handler = self.jit_handlers[key]
			#print 'activating %s with %r' % (key, handler)
			handler(self)
	
	def set_jit(self, key, handler):
		"""
		Configure a handler for a JIT environment variable.
		"""
		self.jit_handlers[key] = handler
	
	def get_resource(self):
		"""
		Return the Resource object this Request refers to.
		
		The
		"""
		if(self.rsrc):
			return self.rsrc
		
		rsrc, self.prepath, self.postpath = self.app.tree.parse(self.path)
		
		if not(rsrc):
			raise404("No such resource: %s" % self['REQUEST_URI'])
		
		self.rsrc = rsrc[0](*rsrc[1], **rsrc[2])
		
		return self.rsrc
	
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
			if(isinstance(fragment, (list, tuple))):
				return '/'.join(fragment)
			
			fragment = str(fragment)
			if(fragment.startswith('/')):
				return fragment[1:]
			else:
				return fragment
		
		args = [_deslash(a) for a in args]
		result = os.path.join(self.app.base_path, *args)
		
		if(self.app.base_path == '/' and not args):
			result = ''
		
		domain = self.get('HTTP_X_FORWARDED_SERVER', self.get('HTTP_HOST', self.app.base_domain))
		
		prefix = '%s://%s' % (self['wsgi.url_scheme'], domain)
		if('HTTP_X_FORWARDED_SERVER' not in self):
			if('SERVER_PORT' in self and domain.find(':') == -1
				and self['SERVER_PORT'] != '80' and self['SERVER_PORT'] != '443'):
				prefix += ':' + self['SERVER_PORT']
		
		result = prefix + result
		
		if('url_rewriter' in self):
			result = self['url_rewriter'](self, result)
		
		return result
	
	def add_header(self, header, data):
		"""
		Store headers for later retrieval.
		"""
		self.response_headers.append((header, str(data)))
	
	def has_header(self, header):
		"""
		Check if a header has ever been set.
		"""
		for h, d in self.response_headers:
			if(h.lower() == header.lower()):
				return True
		return False
	
	def get_headers(self):
		"""
		Get accumulated headers
		"""
		return self.response_headers
	
	def get_header(self, header):
		result = []
		for item in self.response_headers:
			if(item[0].lower() == header.lower()):
				result.append(item[1])
		if not(result):
			raise AttributeError('No such header: %s' % header)
		return result
	

class UnparsedRequest(server.Request):
	"""
	This Request subclass omits the request body parsing that
	happens before our code takes over. This lets us use the
	NestedFieldStorage (or alternative) to parse the body.
	"""
	def requestReceived(self, command, path, version):
		"""Called by channel when all data has been received.
		
		This method is not intended for users.
		"""
		self.content.seek(0,0)
		self.args = {}
		self.stack = []
		
		self.method, self.uri = command, path
		self.clientproto = version
		x = self.uri.split('?', 1)
		
		if len(x) == 1:
			self.path = self.uri
		else:
			self.path, argstring = x
			#self.args = parse_qs(argstring, 1)
		
		# cache the client and server information, we'll need this later to be
		# serialized and sent with the request so CGIs will work remotely
		self.client = self.channel.transport.getPeer()
		self.host = self.channel.transport.getHost()
		
		self.process()

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
		self.__dict__['config'] = {}
		
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
		
		self.approot = get_default_approot(site)
		
		site.initialize(self)
	
	def __setattr__(self, key, value):
		self.config[key] = value
	
	def __getattr__(self, key):
		if(key.startswith('_')):
			return super(Application, self).__getattr__(key)
		return self.__dict__['config'][key]
	
	def activate(self, rsrc, *args, **kwargs):
		"""
		Add a resource to this site's URLNode tree
		"""
		if not resource.IResource.implementedBy(rsrc):
			raise TypeError('%r does not implement IResource' % rsrc)
		
		for path in rsrc(*args, **kwargs).get_paths():
			self.tree.register(path, (rsrc, args, kwargs))
	
	def get_tree(self):
		"""
		Return this site's URLNode tree
		"""
		return self.tree
