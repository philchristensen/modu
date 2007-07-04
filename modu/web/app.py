# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import url
from modu.web import session, wsgi, user
from modu.web.resource import IController
from modu import persist

from twisted import plugin
from zope import interface

import sys, os, copy

host_trees = {}
db_pool = {}

def get_application(env):
	"""
	Return an application object for the site configured
	at the path specified in env.
	
	Note that ISite plugins are only searched when the
	specified host/path is not found.
	"""
	global host_trees
	
	host = env.get('HTTP_HOST', env['SERVER_NAME'])
	
	if not(host in host_trees):
		_load_plugins(env)
	
	host_tree = host_trees[host]
	
	if not(host_tree.has_path(env['SCRIPT_NAME'])):
		_load_plugins(env)
	
	app = host_tree.get_data_at(env['SCRIPT_NAME'])
	return copy.deepcopy(app)

def _load_plugins(env):
	global host_trees
	
	if(env['SCRIPT_FILENAME'] not in sys.path):
		sys.path.append(env['SCRIPT_FILENAME'])
	
	import modu.plugins
	reload(modu.plugins)
	
	for site_plugin in plugin.getPlugins(ISite, modu.plugins):
		app = Application()
		site = site_plugin()
		site.configure_app(app)
		host_tree = host_trees.setdefault(app.base_domain, url.URLNode())
		host_tree.register(app.base_path, app, clobber=True)

class ISite(interface.Interface):
	"""
	An ISitePlugin defines an application that responds to
	a certain hostname and/or path.
	"""
	def configure_app(self, app):
		"""
		Configure the application object for this site.
		"""

class Application(object):
	"""
	An 'application' in the modu universe is simply a place
	to store static configuration data about a particular
	hostname and path on a webserver.
	
	When writing ISite plugins, you'll be populating an empty
	instance of this class, which will be cloned and stored
	in the request object for each page request.
	"""
	def __init__(self):
		_dict = self.__dict__
		_dict['config'] = {}
		
		self.base_domain = 'localhost'
		self.base_path = '/'
		self.db_url = 'mysql://modu:modu@localhost/modu'
		self.session_class = session.DbUserSession
		self.initialize_store = True
		self.default_guid_table = 'guid'
		self.webroot = 'webroot'
		self.debug_session = False
		self.debug_store = False
		self.enable_anonymous_users = True
		self.disable_session_users = False
		
		_dict['_site_tree'] = url.URLNode()
		_dict['_response_headers'] = []
	
	def __setattr__(self, key, value):
		self.config[key] = value
	
	def __getattr__(self, key):
		return self.__dict__['config'][key]
	
	def activate(self, controller):
		"""
		Add a resource to this site's URLNode tree
		"""
		if not IController.providedBy(controller):
			raise TypeError('%r does not implement IController' % controller)
		
		for path in controller.get_paths():
			self._site_tree.register(path, controller)
	
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
		# Databases are a slightly special case. Since we want to re-use
		# db connections as much as possible, we keep the current connection
		# as a global variable. Ordinarily this is a naughty-no-no in mod_python,
		# but we're going to be very very careful.
		db_url = req['modu.app'].db_url
		if(db_url):
			if('__default__' not in db_pool):
				dsn = url.urlparse(req['modu.app'].db_url)
				if(dsn['scheme'] == 'mysql'):
					import MySQLdb
					db_pool['__default__'] = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
				else:
					raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
			
			req['modu.db'] = db_pool['__default__']
		
		initialize_store = req['modu.app'].initialize_store
		if('modu.db' in req and initialize_store):
			# FIXME: I really can't think of any scenario where a store will
			# already be initialized, but we'll check anyway, for now
			store = persist.get_store()
			if not(store):
				if(req['modu.app'].debug_store):
					debug_file = req['wsgi.errors']
				else:
					debug_file = None
				store = persist.Store(req['modu.db'], guid_table=self.default_guid_table, debug_file=debug_file)
			req['modu.store'] = store
		
		# FIXME: We assume that any session class requires database access, and pass
		# the db connection as the second paramter to the session class constructor
		session_class = req['modu.app'].session_class
		if(db_url and session_class):
			req['modu.session'] = session_class(req, req['modu.db'])
			if(req['modu.app'].debug_session):
				req.log_error('session contains: ' + str(req['modu.session']))
			if(self.disable_session_users):
				if(self.enable_anonymous_users):
					req['modu.user'] = user.AnonymousUser()
				else:
					req['modu.user'] = None
			else:
				req['modu.user'] = req['modu.session'].get_user()
				if(req['modu.user'] is None and self.enable_anonymous_users):
					req['modu.user'] = user.AnonymousUser()
		
