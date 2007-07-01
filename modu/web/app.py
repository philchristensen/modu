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

import sys, os

host_trees = {}

def desperate_apache_log(msg):
	try:
		from mod_python import apache
		apache.log_error(('[modu-%d] ' % os.getpid()) + str(msg))
	except:
		pass

def get_application(env):
	if(env['SCRIPT_FILENAME'] not in sys.path):
		#desperate_apache_log('added ' + env['SCRIPT_FILENAME'] + ' to path')
		sys.path.append(env['SCRIPT_FILENAME'])
	
	load_plugins()
	
	host = env.get('HTTP_HOST', env['SERVER_NAME'])
	
	global host_trees
	if not(host in host_trees):
		return None
	
	#desperate_apache_log('searching for host: ' + host)
	#desperate_apache_log('searching for path: ' + env['SCRIPT_NAME'])
	
	host_tree = host_trees[host]
	#desperate_apache_log('host tree is: ' + str(host_tree))
	app = host_tree.parse(env['SCRIPT_NAME'])
	
	#if(app):
	#	desperate_apache_log('found app: ' + str(app))
	
	return app

def load_plugins():
	global host_trees
	import modu.plugins
	reload(modu.plugins)
	
	# # FIXME: regenerate the cache
	try:
		list(plugin.getPlugins(plugin.IPlugin, modu.plugins))
	except:
		pass
	#desperate_apache_log('plugin __path__ is: ' + str(modu.plugins.__path__))
	for site_plugin in plugin.getPlugins(ISite, modu.plugins):
		app = Application()
		site = site_plugin()
		#desperate_apache_log('loading site plugin: ' + repr(site))
		site.configure_app(app)
		host_tree = host_trees.setdefault(app.base_domain, url.URLNode())
		#desperate_apache_log('host tree is: ' + str(host_trees[app.base_domain]))
		# NOTE: remember, python state may or may not stick around
		if not(host_tree.has_path(app.base_path)):
			host_tree.register(app.base_path, app)
		#else:
		#	desperate_apache_log('already exists app with base path: ' + app.base_path)

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
		_dict['_db'] = None
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
		return self._site_tree
	
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
		if(not self._db and db_url):
			dsn = url.urlparse(req['modu.config.db_url'])
			if(dsn['scheme'] == 'mysql'):
				import MySQLdb
				self._db = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
			else:
				raise NotImplementedError("Unsupported database driver: '%s'" % dsn['scheme'])
		req['modu.db'] = self._db
		
		# FIXME: We assume that any session class requires database access, and pass
		# the db connection as the second paramter to the session class constructor
		session_class = req['modu.config.session_class']
		if(db_url and session_class):
			req['modu.session'] = session_class(req, req['modu.db'])
			if(req['modu.config.debug_session']):
				req.log_error('session contains: ' + str(req['modu.session']))
		
		initialize_store = req['modu.config.initialize_store']
		if(self._db):
			# FIXME: I really can't think of any scenario where a store will
			# already be initialized, but we'll check anyway, for now
			store = persist.get_store()
			if not(store):
				if(req['modu.config.debug_store']):
					debug_file = req['wsgi.errors']
				else:
					debug_file = None
				global default_guid_table
				store = persist.Store(self._db, guid_table=default_guid_table, debug_file=debug_file)
			req['modu.store'] = store
