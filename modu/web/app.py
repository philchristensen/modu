# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import url
from modu.web import session, wsgi
from modu import persist

from twisted import plugin
from zope import interface

import sys, os, copy

host_trees = {}
db_pool = {}

def get_application(env):
	load_plugins(env)
	
	host = env.get('HTTP_HOST', env['SERVER_NAME'])
	
	global host_trees
	if not(host in host_trees):
		return None
	
	host_tree = host_trees[host]
	app = host_tree.get_data_at(env['SCRIPT_NAME'])
	
	return app

def load_plugins(env):
	global host_trees
	
	if(env['SCRIPT_FILENAME'] not in sys.path):
		sys.path.append(env['SCRIPT_FILENAME'])
	
	import modu.plugins as modu_plugins
	reload(modu_plugins)
	
	for site_plugin in plugin.getPlugins(ISite, modu_plugins):
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
		Configure an application object for this site.
		"""

class IPlugin(interface.Interface):
	def menu(self):
		"""
		Return an array of resources.
		"""

class Application(object):
	def __init__(self):
		_dict = self.__dict__
		_dict['config'] = {}
		
		_dict['config']['base_domain'] = 'localhost'
		_dict['config']['base_path'] = '/'
		_dict['config']['db_url'] = 'mysql://modu:modu@localhost/modu'
		_dict['config']['session_class'] = session.UserSession
		_dict['config']['initialize_store'] = True
		_dict['config']['default_guid_table'] = 'guid'
		_dict['config']['webroot'] = 'webroot'
		_dict['config']['debug_session'] = False
		_dict['config']['debug_store'] = False
		
		_dict['_site_tree'] = url.URLNode()
		_dict['_response_headers'] = []
	
	def __setattr__(self, key, value):
		self.config[key] = value
	
	def __getattr__(self, key):
		return self.__dict__['config'][key]
	
	def activate(self, rsrc):
		"""
		Add a resource to this site's URLNode tree
		"""
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
	
	def load_config(self, req):
		"""
		Load this app's configuration variables into the
		provided request object.
		"""
		for key in self.config:
			req['modu.config.' + key] = self.config[key]
	
	def bootstrap(self, req):
		"""
		Initialize the common services, store them in the
		provided request variable.
		"""
		# Databases are a slightly special case. Since we want to re-use
		# db connections as much as possible, we keep the current connection
		# as a global variable. Ordinarily this is a naughty-no-no in mod_python,
		# but we're going to be very very careful.
		db_url = req['modu.config.db_url']
		if(db_url):
			if('__default__' not in db_pool):
				dsn = url.urlparse(req['modu.config.db_url'])
				if(dsn['scheme'] == 'mysql'):
					import MySQLdb
					db_pool['__default__'] = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
				else:
					raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
			
			req['modu.db'] = db_pool['__default__']
		
		# FIXME: We assume that any session class requires database access, and pass
		# the db connection as the second paramter to the session class constructor
		session_class = req['modu.config.session_class']
		if(db_url and session_class):
			req['modu.session'] = session_class(req, req['modu.db'])
			if(req['modu.config.debug_session']):
				req.log_error('session contains: ' + str(req['modu.session']))
		
		initialize_store = req['modu.config.initialize_store']
		if('modu.db' in req and initialize_store):
			# FIXME: I really can't think of any scenario where a store will
			# already be initialized, but we'll check anyway, for now
			store = persist.get_store()
			if not(store):
				if(req['modu.config.debug_store']):
					debug_file = req['wsgi.errors']
				else:
					debug_file = None
				store = persist.Store(req['modu.db'], guid_table=self.default_guid_table, debug_file=debug_file)
			req['modu.store'] = store
