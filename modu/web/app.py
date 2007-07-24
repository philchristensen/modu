# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os, os.path, sys, stat, copy, mimetypes, traceback

from modu.util import url, tags
from modu.web import session, user, resource
from modu import persist, web

from twisted import plugin
from zope import interface

host_trees = {}
db_pool = {}

def handler(env, start_response):
	try:
		sanity_check(env)
	except Exception, e:
		start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
		return [content500(env['REQUEST_URI'], e)]
	
	application = get_application(env)
	env['modu.app'] = application
	req = configure_request(env)
	
	if not(application):
		start_response('404 Not Found', [('Content-Type', 'text/html')])
		return [content404(env['REQUEST_URI'])]
	
	application.bootstrap(req)
	result = check_file(req)
	if(result):
		content = [content403(env['REQUEST_URI'])]
		headers = []
		if(result[1]):
			try:
				content = req['wsgi.file_wrapper'](open(result[0]))
			except:
				status = '403 Forbidden'
				headers.append(('Content-Type', 'text/html'))
			else:
				status = '200 OK'
				headers.append(('Content-Type', result[1]))
				headers.append(('Content-Length', result[2]))
		else:
			status = '403 Forbidden'
			headers.append(('Content-Type', 'text/html'))
		start_response(status, application.get_headers())
		return content
	
	tree = application.get_tree()
	rsrc = tree.parse(req['modu.path'])
	if not(rsrc):
		start_response('404 Not Found', [('Content-Type', 'text/html')])
		return [content404(env['REQUEST_URI'])]
	
	req['modu.tree'] = tree
	
	try:
		try:
			if(resource.IResourceDelegate.providedBy(rsrc)):
				rsrc = rsrc.get_delegate(req)
			if(resource.IAccessControl.providedBy(rsrc)):
				rsrc.check_access(req)
			content = rsrc.get_response(req)
		except web.HTTPStatus, http:
			start_response(http.status, http.headers)
			return http.content
	finally:
		if('modu.session' in req):
			req['modu.session'].save()
	
	start_response('200 OK', application.get_headers())
	return [content]


def sanity_check(env):
	if(env['wsgi.multithread']):
		raise EnvironmentError("""Sorry, modu does not support multithreaded
		web containers at this time. If you are using Apache 2, please make
		sure you're using the Prefork MPM.""")


def configure_request(env):
	# Hopefully the next release of mod_python
	# will let us ditch this line
	env['SCRIPT_NAME'] = env['modu.app'].base_path
	
	# once the previous line is gone, this next
	# block should be able to be moved elsewhere
	uri = env['REQUEST_URI']
	if(uri.startswith(env['SCRIPT_NAME'])):
		env['PATH_INFO'] = uri[len(env['SCRIPT_NAME']):]
	else:
		env['PATH_INFO'] = uri
	
	env['modu.approot'] = env['SCRIPT_FILENAME']
	env['modu.path'] = env['PATH_INFO']
	
	approot = env['modu.approot']
	webroot = env['modu.app'].webroot
	webroot = os.path.join(approot, webroot)
	env['PATH_TRANSLATED'] = os.path.realpath(webroot + env['modu.path'])
	
	return Request(env)


def check_file(req):
	true_path = req['PATH_TRANSLATED']
	try:
		finfo = os.stat(true_path)
		# note that there's no support for directory indexes,
		# only direct file access under the webroot
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


def get_application(req):
	"""
	Return an application object for the site configured
	at the path specified in req.
	
	Note that ISite plugins are only searched when the
	specified host/path is not found.
	"""
	global host_trees
	
	host = req.get('HTTP_HOST', req['SERVER_NAME'])
	
	if not(host in host_trees):
		_scan_plugins(req)
	
	host_tree = host_trees[host]
	
	if not(host_tree.has_path(req['SCRIPT_NAME'])):
		_scan_plugins(req)
	
	app = host_tree.get_data_at(req['SCRIPT_NAME'])
	
	return copy.deepcopy(app)


def content404(path=None):
	content = tags.h1()['Not Found']
	content += tags.hr()
	content += tags.p()['There is no object registered at that path.']
	if(path):
		content += tags.strong()[path]
	return content


def content403(path=None):
	content = tags.h1()['Forbidden']
	content += tags.hr()
	content += tags.p()['You are not allowed to access that path.']
	if(path):
		content += tags.strong()[path]
	return content


def content401(path=None):
	content = tags.h1()['Unauthorized']
	content += tags.hr()
	content += tags.p()['You have not supplied the appropriate credentials.']
	if(path):
		content += tags.strong()[path]
	return content


def content500(path=None, exception=None):
	content = tags.h1()['Internal Server Error']
	content += tags.hr()
	content += tags.p()['Sorry, an error has occurred:']
	content += tags.pre()[traceback.format_exc()]
	if(path):
		content += tags.strong()[path]
	return content


def _scan_plugins(req):
	global host_trees
	
	if(req['SCRIPT_FILENAME'] not in sys.path):
		sys.path.append(req['SCRIPT_FILENAME'])
	
	import modu.plugins
	reload(modu.plugins)
	
	for site_plugin in plugin.getPlugins(ISite, modu.plugins):
		site = site_plugin()
		app = Application(site)
		host_tree = host_trees.setdefault(app.base_domain, url.URLNode())
		host_tree.register(app.base_path, app, clobber=True)


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
	
	def __getattr__(self, key):
		if(key in self):
			return self[key]
		elif(key.find('_') != -1):
			return self[key.replace('_', '.')]
		raise AttributeError(key)
	
	def log_error(self, data):
		self['wsgi.errors'].write(data)
	
	def has_form_data(self):
		if(self['REQUEST_METHOD'] == 'POST'):
			return True
		elif(self['QUERY_STRING']):
			return True
		return False


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
		_dict['config'] = {}
		
		self.base_domain = 'localhost'
		self.base_path = '/'
		self.db_url = 'mysql://modu:modu@localhost/modu'
		self.session_class = session.DbUserSession
		self.initialize_store = True
		self.webroot = 'webroot'
		self.debug_session = False
		self.debug_store = False
		self.enable_anonymous_users = True
		self.disable_session_users = False
		
		_dict['_site_tree'] = url.URLNode()
		_dict['_response_headers'] = []
		_dict['_site'] = site
		
		site.initialize(self)
	
	def __setattr__(self, key, value):
		self.config[key] = value
	
	def __getattr__(self, key):
		return self.__dict__['config'][key]
	
	def activate(self, rsrc):
		"""
		Add a resource to this site's URLNode tree
		"""
		if not resource.IResource.providedBy(rsrc):
			raise TypeError('%r does not implement IResource' % rsrc)
		
		for path in rsrc.get_paths():
			self._site_tree.register(path, rsrc)
	
	def get_tree(self):
		"""
		Return this site's URLNode tree
		"""
		return copy.deepcopy(self._site_tree)
	
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
	
	def bootstrap(self, req):
		"""
		Initialize the common services, store them in the
		provided request variable.
		"""
		db_url = req['modu.app'].db_url
		if(db_url):
			if('__default__' not in db_pool):
				dsn = url.urlparse(req['modu.app'].db_url)
				if(dsn['scheme'] == 'mysql'):
					from modu.persist import mysql
					db_pool['__default__'] = mysql.connect(dsn)
				else:
					raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
			
			req['modu.db'] = db_pool['__default__']
		
		persist.activate_store(req)
		session.activate_session(req)
