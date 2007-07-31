# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.enterprise import adbapi

from modu.util import url

def connect(db_url, async=False, **kwargs):
	dsn = get_dsn(db_url)
	kwargs.update(dsn)
	if(async):
		return adbapi.ConnectionPool(**kwargs)
	else:
		return SynchronousConnectionPool(**kwargs)

def get_dsn(db_url):
	dsn = url.urlparse(db_url)
	
	for key in dsn.keys():
		if(dsn[key] is None):
			del dsn[key]
	
	if(dsn['scheme'] == 'MySQLdb'):
		dsn['cp_openfun'] = fix_mysqldb
		from MySQLdb import cursors
		dsn['cursorclass'] = cursors.SSDictCursor

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
	from distutils.version import LooseVersion
	import MySQLdb
	"""
	fix character_set_name() bug in MySQLdb < 1.2.2
	"""
	if(LooseVersion(MySQLdb.__version__) < LooseVersion('1.2.2')):
		def _yes_utf8_really(self):
			return 'utf-8'
		
		instancemethod = type(_DummyClass._dummy_method)
		
		connection.character_set_name = instancemethod(_yes_utf8_really, connection, connection.__class__)


class SynchronousConnectionPool(adbapi.ConnectionPool):
	def __init__(self, dbapiName, *connargs, **connkw):
		adbapi.ConnectionPool.__init__(self, dbapiName, *connargs, **connkw)
		from twisted.internet import reactor
		reactor.removeSystemEventTrigger(self.startID)
	
	def runInteraction(self, interaction, *args, **kw):
		return self._runInteraction(interaction, *args, **kw)
	
	def runWithConnection(self, func, *args, **kw):
		return self._runWithConnection(func, *args, **kw)


class _DummyClass(object):
	def _dummy_method(self):
		pass