# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.enterprise import adbapi

from modu.util import url

def connect(db_url, async=False, **kwargs):
	"""
	Accepts a DSN specified as a URL, and returns a new
	connection pool object. If `async` is False (the default),
	all database requests are made synchronously.
	"""
	dsn = get_dsn(db_url)
	kwargs.update(dsn)
	if(async):
		return adbapi.ConnectionPool(**kwargs)
	else:
		return SynchronousConnectionPool(**kwargs)

def get_dsn(db_url):
	"""
	Take a database URL, parse it, and modify it slightly
	so it may be passed as **kwargs to the DB-API connect()
	function.
	"""
	dsn = url.urlparse(db_url)
	
	for key in dsn.keys():
		if(dsn[key] is None):
			del dsn[key]
	
	if(dsn['scheme'] == 'MySQLdb'):
		dsn['cp_openfun'] = fix_mysqldb
		from MySQLdb import cursors
		dsn['cursorclass'] = cursors.SSDictCursor
		#dsn['use_unicode'] = True
		#dsn['charset'] = 'utf8'

	dsn['dbapiName'] = dsn['scheme']
	del dsn['scheme']
	
	dsn['db'] = dsn['path'][1:]
	del dsn['path']
	
	dsn['cp_reconnect'] = True
	dsn['cp_noisy'] = True
	dsn['cp_min'] = 10
	dsn['cp_max'] = 15
	
	return dsn

def fix_mysqldb(connection):
	"""
	This function takes a MySQLdb connection object and replaces
	character_set_name() if the version of MySQLdb < 1.2.2.
	"""
	from distutils.version import LooseVersion
	import MySQLdb
	if(LooseVersion(MySQLdb.__version__) < LooseVersion('1.2.2')):
		def _yes_utf8_really(self):
			return 'utf8'
		print 'Fixed broken MySQLdb client'
		instancemethod = type(_DummyClass._dummy_method)
		
		connection.character_set_name = instancemethod(_yes_utf8_really, connection, connection.__class__)


class SynchronousConnectionPool(adbapi.ConnectionPool):
	"""
	This trvial subclass disables thread creation within the ConnectionPool
	object so that it may be used from within a syncronous application
	"""
	def __init__(self, dbapiName, *connargs, **connkw):
		adbapi.ConnectionPool.__init__(self, dbapiName, *connargs, **connkw)
		from twisted.internet import reactor
		if(self.startID):
			reactor.removeSystemEventTrigger(self.startID)
	
	def runInteraction(self, interaction, *args, **kw):
		return self._runInteraction(interaction, *args, **kw)
	
	def runWithConnection(self, func, *args, **kw):
		return self._runWithConnection(func, *args, **kw)


class _DummyClass(object):
	"""
	Dummy class used to override an instance method on MySQLdb connection object.
	@seealso C{fix_mysqldb()}
	"""
	def _dummy_method(self):
		pass