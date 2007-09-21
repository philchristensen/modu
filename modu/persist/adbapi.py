# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Provides synchronous access to the Twisted adbapi DB layer.
"""

from twisted.enterprise import adbapi

from modu.util import url

def connect(db_url=None, async=False, *args, **kwargs):
	"""
	Accepts a DSN specified as a URL, and returns a new
	connection pool object. If `async` is False (the default),
	all database requests are made synchronously.
	"""
	if(db_url is not None):
		dsn = get_dsn(db_url)
		
		dbapiName = dsn['dbapiName']
		del dsn['dbapiName']
		
		globs = {}
		exec('from modu.persist import adbapi_%s as db_driver' % dbapiName, globs)
		dargs, dkwargs = globs['db_driver'].process_dsn(dsn)
		kwargs.update(dkwargs)
		args = list(args)
		args.extend(dargs)
	
	if(async):
		return adbapi.ConnectionPool(dbapiName, *dargs, **dkwargs)
	else:
		return SynchronousConnectionPool(dbapiName, *dargs, **dkwargs)

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
	
	dsn['dbapiName'] = dsn['scheme']
	del dsn['scheme']
	
	dsn['db'] = dsn['path'][1:]
	del dsn['path']
	
	dsn['cp_reconnect'] = True
	dsn['cp_noisy'] = False
	dsn['cp_min'] = 10
	dsn['cp_max'] = 15
	
	return dsn

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
	
	# def runOperation(self, *args, **kwargs):
	# 	print args, kwargs
	# 	adbapi.ConnectionPool.runOperation(self, *args, **kwargs)
	# 
	# def runQuery(self, *args, **kwargs):
	# 	print args, kwargs
	# 	return adbapi.ConnectionPool.runQuery(self, *args, **kwargs)
	
	def runInteraction(self, interaction, *args, **kw):
		return self._runInteraction(interaction, *args, **kw)
	
	def runWithConnection(self, func, *args, **kw):
		return self._runWithConnection(func, *args, **kw)
	
	def _runInteraction(self, interaction, *args, **kw):
		conn = adbapi.Connection(self)
		trans = adbapi.Transaction(self, conn)
		try:
			result = interaction(trans, *args, **kw)
			if(result and isinstance(result[0], (list, tuple))):
				result = [dict(zip([c[0] for c in trans._cursor.description], item)) for item in result]
			trans.close()
			conn.commit()
			return result
		except:
			conn.rollback()
			raise
