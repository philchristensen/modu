
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

@var pools: map of synchronous database connections, shared between threads
@type pools: dbapi.SynchronousConnectionPool

@var pools_lock: lock on pools during site configuration
@type pools_lock: threading.BoundedSemaphore
"""

import os, os.path, sys, stat, copy
import mimetypes, traceback, threading, urllib

from modu import persist, web
from modu.util import url, tags, queue, form
from modu.web import session, user, resource, static
from modu.persist import dbapi

from twisted import plugin
from twisted.web import server
from twisted.python import failure
from twisted.web.util import formatFailure, htmlReprTypes, htmlDict
from zope import interface

host_tree = {}
host_tree_lock = threading.BoundedSemaphore()

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
				application.make_immutable()
				req = configure_request(env, application)
			else:
				raise404("No such application: %s" % env['REQUEST_URI'])
			
			check_maintenance_mode(req)
			
			if(getattr(application, 'force_sessions', False)):
				# referencing the session will force JIT activation
				req.session
			
			if(hasattr(application.site, 'configure_request')):
				application.site.configure_request(req)
			rsrc = req.get_resource()
			
			if not(rsrc):
				raise404("No such resource: %s" % env['REQUEST_URI'])
			
			if(resource.IResourceDelegate.providedBy(rsrc)):
				rsrc = rsrc.get_delegate(req)
			
			req['modu.resource'] = rsrc
			content = rsrc.get_response(req)
		finally:
			# remember, req.get will return None if the session wasn't used
			# in this page load
			if(req.get('modu.session', None) is not None):
				req.session.save()
	except web.HTTPStatus, http:
		reason = failure.Failure()
		
		headers = http.headers
		if(application):
			headers += req.get_headers()
		content = http.content
		
		if('modu.app' in req and req.app.config.get('status_content')):
			content_provider = req.app.status_content()
			if(hasattr(content_provider, 'handles_status') and content_provider.handles_status(http)):
				req['modu.failure'] = reason
				content_provider.prepare_content(req)
				content = [content_provider.get_content(req)]
		
		start_response(http.status, headers)
		return content
	except web.MaintenanceMode, maintenance:
		# note that we don't check for modu.app existing here
		# as our check happens after we create it (otherwise,
		# we assume an error would have occurred)
		if(req.app.config.get('maintenance_content')):
			content_provider = req.app.maintenance_content()
			content_provider.prepare_content(req)
			content = [content_provider.get_content(req)]
			headers = [('Content-Type', content_provider.get_content_type(req))]
		else:
			content = ["<html><head><title>Maintenance Mode</title></head>"
					"<body>Sorry, the server is currently undergoing maintenance, "
					"please come back soon.</body></html>\n"]
			headers = [('Content-Type', 'text/html')]
		
		start_response('503 Service Unavailable', headers)
		return content
	except:
		reason = failure.Failure()
		reason.printTraceback(env['wsgi.errors'])
		if('modu.app' in req and req.app.config.get('error_content')):
			content_provider = req.app.error_content()
			req['modu.failure'] = reason
			content_provider.prepare_content(req)
			content = [content_provider.get_content(req)]
			headers = [('Content-Type', content_provider.get_content_type(req))]
		else:
			content = ["<html><head><title>web.Server Traceback (most recent call last)</title></head>"
				"<body><b>web.Server Traceback (most recent call last):</b>\n\n"
				"%s\n\n</body></html>\n" % formatFailure(reason)]
			headers = [('Content-Type', 'text/html')]
		
		start_response('500 Internal Server Error', headers)
		return content
	
	start_response('200 OK', req.get_headers())
	return content

def check_maintenance_mode(req):
	"""
	Check whether maintenance mode is on or not.
	
	At this time, this merely checks for the existence of a 'modu-maintenance' file
	in /etc. There are a significant limitations with this implementation:
	
	 -  This affects *all* applications running in this instance.
	 -  It's not possible to fetch any kind of resource, since the
	    maintenance page is returned for *all* URLs.
	"""
	if(os.path.exists('/etc/modu-maintenance')):
		raise web.MaintenanceMode()

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
		uri, qs = env['REQUEST_URI'].split('?', 1)
	
	if(uri.startswith(env['SCRIPT_NAME'])):
		env['PATH_INFO'] = uri[len(env['SCRIPT_NAME']):]
	else:
		env['PATH_INFO'] = uri
	
	if not(env['PATH_INFO'].startswith('/')):
		env['PATH_INFO'] = '/' + env['PATH_INFO']
	
	env['modu.approot'] = application.approot
	env['modu.path'] = env['PATH_INFO']
	
	webroot = os.path.join(application.approot, application.webroot)
	env['PATH_TRANSLATED'] = os.path.realpath(os.path.join(webroot, env['modu.path'][1:]))
	
	req = Request(env)
	
	if(req.app.db_url):
		req.set_jit('modu.pool', dbapi.activate_pool)
	if(req.app.db_url and application.initialize_store):
		req.set_jit('modu.store', persist.activate_store)
	if(req.app.db_url and req.app.session_class):
		req.set_jit('modu.session', session.activate_session)
		req.set_jit('modu.user', session.activate_session)
	if not(req.app.disable_message_queue):
		req.set_jit('modu.messages', queue.activate_messages)
	
	req.set_jit('modu.data', form.activate_field_storage)
	req.set_jit('modu.content', queue.activate_content_queue)
	
	return req

def get_default_approot(site):
	"""
	Get the application root of the provided site configuration.
	
	Note that use of approot and webroot are increasingly discouraged,
	since the current implementation makes significant assumptions
	about how your application code is installed.
	
	The approot is assumed to be two directories up from where the
	site configuration class file is found. 
	"""
	parts = site.__class__.__module__.split('.')
	# I left off the part that forces absolute imports, so this will work in py 2.4
	package = __import__('.'.join(parts[:-1]), globals(), locals(), parts[-1])
	mod = getattr(package, parts[-1])
	return os.path.abspath(os.path.dirname(os.path.abspath(mod.__file__)) + '/../..')

def get_normalized_hostname(env):
	"""
	Get the best hostname we can find in the provided environment.
	
	If the request came in on an alternate port, it will be
	appended to the result.
	"""
	host = env.get('HTTP_HOST', env['SERVER_NAME'])
	if(host.find(':') == -1):
		host += ':' + env['SERVER_PORT']
	return host

def get_process_info():
	"""
	Debug info table that can be appended to error output.
	Currently unused (a potential security risk, but good for debugging)
	"""
	import thread
	return tags.table()[[
		tags.tr()[[
			tags.th()['Thread Name:'],
			tags.td()[thread.get_ident()]
		]],
		tags.tr()[[
			tags.th()['Process ID:'],
			tags.td()[os.getpid()]
		]],
		tags.tr()[[
			tags.th()['Python Path:'],
			tags.td()[str(sys.path)]
		]],
		tags.tr()[[
			tags.th()['Site Tree:'],
			tags.td()[tags.encode_htmlentities(str(host_tree))]
		]],
	]]

def get_application(env):
	"""
	Return an application object for the site configured
	at the path specified in env.
	
	Note that ISite plugins are only searched when the
	specified host/path is not found.
	"""
	global host_tree
	
	host = get_normalized_hostname(env)
	
	if('MODU_PATH' in env):
		sys.path.extend(env['MODU_PATH'].split(':'))
	
	if('REQUEST_URI' not in env):
		if(env['PATH_INFO']):
			env['REQUEST_URI'] = os.path.join(env['SCRIPT_NAME'], env['PATH_INFO'])
		else:
			env['REQUEST_URI'] = env['SCRIPT_NAME']
	
	host_tree_lock.acquire()
	try:
		if not(host in host_tree):
			_scan_sites(env)
		if not(host in host_tree):
			return None
		
		host_node = host_tree[host]
		
		if not(host_node.has_path(env['REQUEST_URI'])):
			_scan_sites(env)
		
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
	content += tags.hr()
	#content += get_process_info()
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

def raise400(path=None):
	"""
	Bad Request
	"""
	content = tags.h1()['Bad Request']
	content += tags.hr()
	content += tags.p()['Your browser sent an invalid request.']
	if(path):
		content += tags.strong()[path]
	raise web.HTTPStatus('400 Bad Request', [('Content-Type', 'text/html')], [content])

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

def _scan_sites(env):
	"""
	Search for available site configuration objects.
	
	Register any found objects with the internal structures.
	"""
	global host_tree
	
	import modu.sites
	reload(modu.sites)
	
	plugins = plugin.getPlugins(ISite, modu.sites)
	
	for site_plugin in plugins:
		site = site_plugin()
		app = Application(site)
		
		root = app.tree.get_data_at('/')
		webroot = os.path.join(app.approot, app.webroot)
		app.tree.register('/', (static.FileResource, (webroot, root), {}), clobber=True)
		
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
	def initialize(app):
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
		self['modu.prepath'] = []
		self['modu.postpath'] = []
		
		self.update(env)
		self.rsrc = None
		self.jit_handlers = {}
		
		self.response_headers = []
	
	def simplify(self):
		result = self.copy()
		
		result['modu.prepath'] = '/'.join(result['modu.prepath'])
		result['modu.postpath'] = '/'.join(result['modu.postpath'])
		
		for k, v in result.items():
			if not(isinstance(v, basestring)):
				del result[k]
		
		return result
	
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
		
		Until this method is called, the prepath and postpath member
		variables are uninitialized.
		"""
		if(self.rsrc):
			return self.rsrc
		
		rsrc, self['modu.prepath'], self['modu.postpath'] = self.app.tree.parse(self.path)
		
		if not(rsrc):
			raise404("No such resource: %s" % self['REQUEST_URI'])
		
		self.rsrc = rsrc[0](*rsrc[1], **rsrc[2])
		
		return self.rsrc
	
	def log_error(self, data):
		"""
		Log an error to the WSGI standard error log.
		"""
		self['wsgi.errors'].write(str(data))
	
	def has_form_data(self):
		"""
		Returns True if the REQUEST_METHOD is POST, or there is a query string provided.
		"""
		if(self['REQUEST_METHOD'] == 'POST'):
			return True
		elif(self['QUERY_STRING']):
			return True
		return False
	
	def get_path(self, *args, **query):
		"""
		Assemble an absolute URL for this application.
		"""
		newenv = self.copy()
		if(isinstance(query.get('env', None), dict)):
			env = query.pop('env')
			newenv.update(env)
		env = newenv
		
		def _deslash(fragment):
			if(isinstance(fragment, (list, tuple))):
				return '/'.join(fragment)
			
			fragment = str(fragment)
			if(fragment.startswith('/')):
				return fragment[1:]
			else:
				return fragment
		
		args = [_deslash(a) for a in args]
		result = os.path.join(env['modu.app'].base_path, *args)
		
		if(env['modu.app'].base_path == '/' and not args):
			result = ''
		
		domain = env.get('HTTP_X_FORWARDED_SERVER', env.get('HTTP_HOST', env['modu.app'].base_domain))
		
		prefix = '%s://%s' % (env['wsgi.url_scheme'], domain)
		if('HTTP_X_FORWARDED_SERVER' not in env):
			if(domain.find(':') == -1 and env.get('SERVER_PORT', '80') not in ('80','443')):
				prefix += ':' + env['SERVER_PORT']
		
		result = prefix + result
		if(query):
			result += '?' + urllib.urlencode(query)
		
		if('url_rewriter' in env):
			result = env['url_rewriter'](self, result)
		
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
		"""
		Get the value of a particular previously-set response header.
		"""
		result = []
		for item in self.response_headers:
			if(item[0].lower() == header.lower()):
				result.append(item[1])
		if not(result):
			raise AttributeError('No such header: %s' % header)
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
		self.__dict__['immutable'] = False
		self.__dict__['config'] = {}
		
		self.base_domain = 'localhost'
		self.base_path = '/'
		self.db_url = 'MySQLdb://modu:modu@localhost/modu'
		self.session_class = session.DbUserSession
		self.session_cookie_params = {'Path':'/'}
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
		
	def make_immutable(self):
		self.__dict__['immutable'] = True
	
	def __repr__(self):
		return '<Application object %s>' % repr(self.config)
	
	def __setattr__(self, key, value):
		if(self.immutable):
			raise AttributeError("Application objects are immutable once they've been initialized.")
		self.config[key] = value
	
	def __getattr__(self, key):
		if(not key.startswith('_') and key in self.config):
			return self.config[key]
		else:
			raise AttributeError(key)
	
	def activate(self, paths, rsrc, *args, **kwargs):
		"""
		Add a resource to this site's URLNode tree
		"""
		clobber = kwargs.get('clobber', False)
		kwargs.pop('clobber', None)
		
		if not resource.IResource.implementedBy(rsrc):
			raise TypeError('%r does not implement IResource' % rsrc)
		
		if not(isinstance(paths, (list, tuple))):
			paths = [paths]
		
		for path in paths:
			self.tree.register(path, (rsrc, args, kwargs), clobber=clobber)
	
	def get_tree(self):
		"""
		Return this site's URLNode tree
		"""
		return self.tree

def _applicationDict(app):
	return htmlDict(app.config)

htmlReprTypes[Application] = _applicationDict
htmlReprTypes[Request] = htmlDict

