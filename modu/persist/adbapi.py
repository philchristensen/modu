# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Provides synchronous access to the Twisted adbapi DB layer.
"""

from twisted.enterprise import adbapi

from modu.util import url

debug = False

def connect(db_url=None, async=False, *args, **kwargs):
	"""
	Get a new connection pool for a particular db_url.
	
	Accepts a DSN specified as a URL, and returns a new
	connection pool object. If `async` is False (the default),
	all database requests are made synchronously.
	
	@param db_url: A URL of the form C{drivername://user:password@host/dbname}
	@type db_url: str
	
	@param async: if True, create an asynchronous connection pool object.
	@type async: bool
	
	@param *args: other positional arguments to pass to the DB-API driver.
	@param **kwargs: other keyword arguments to pass to the DB-API driver.
	"""
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
		"""
		Create a new instance of the connection pool.
		
		This overridden constructor makes sure the Twisted reactor
		doesn't get started in non-twisted.web-hosted environments.
		"""
		adbapi.ConnectionPool.__init__(self, dbapiName, *connargs, **connkw)
		from twisted.internet import reactor
		if(self.startID):
			reactor.removeSystemEventTrigger(self.startID)
	
	def runOperation(self, *args, **kwargs):
		"""
		Trivial override to provide debugging support.
		"""
		if(debug):
			print args, kwargs
		adbapi.ConnectionPool.runOperation(self, *args, **kwargs)
	
	def runQuery(self, *args, **kwargs):
		"""
		Trivial override to provide debugging support.
		"""
		if(debug):
			print args, kwargs
		return adbapi.ConnectionPool.runQuery(self, *args, **kwargs)
	
	def runInteraction(self, interaction, *args, **kw):
		"""
		Run a SQL statement through one of the connections in this pool.
		
		This version of the method does not spawn a thread, and so returns
		the result directly, instead of a Deferred.
		"""
		return self._runInteraction(interaction, *args, **kw)
	
	def runWithConnection(self, func, *args, **kw):
		"""
		Run a function, passing it one of the connections in this pool.
		
		This version of the method does not spawn a thread, and so returns
		the result directly, instead of a Deferred.
		"""
		return self._runWithConnection(func, *args, **kw)
	
	def _runInteraction(self, interaction, *args, **kw):
		"""
		An internal function to run a SQL statement through one of the connections in this pool.
		
		This version of the method ensures that all drivers return a column->value dict. This
		can also be handled by the driver layer itself (e.g., by selecting a particular
		cursor type).
		"""
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
