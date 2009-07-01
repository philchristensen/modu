# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Provides synchronous access to the Twisted adbapi DB layer.
"""

import threading, collections

from twisted.enterprise import adbapi

from modu.util import url

debug = False
pools = {}
pools_lock = threading.BoundedSemaphore()

def activate_pool(req):
	"""
	JIT Request handler for enabling DB support.
	"""
	req['modu.pool'] = acquire_db(req.app.db_url)

def acquire_db(db_url):
	"""
	Create the shared connection pool for this process.
	"""
	global pools, pools_lock
	pools_lock.acquire()
	try:
		if(db_url in pools):
			pool = pools[db_url]
		else:
			from modu.persist import dbapi
			pool = dbapi.connect(db_url)
			pools[db_url] = pool
	finally:
		pools_lock.release()
	
	return pool

def connect(db_urls=None, async=False, *args, **kwargs):
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
	if not(isinstance(db_urls, tuple)):
		db_urls = [db_urls]
	
	replicated_pool = None
	for db_url in db_urls:
		dsn = get_dsn(db_url)
		
		dbapiName = dsn['dbapiName']
		del dsn['dbapiName']
		
		globs = {}
		exec('from modu.persist import dbapi_%s as db_driver' % dbapiName, globs)
		dargs, dkwargs = globs['db_driver'].process_dsn(dsn)
		kwargs.update(dkwargs)
		args = list(args)
		args.extend(dargs)
		
		if(async):
			pool = adbapi.ConnectionPool(dbapiName, *dargs, **dkwargs)
		else:
			pool = SynchronousConnectionPool(dbapiName, *dargs, **dkwargs)
		
		if(len(db_urls) == 1):
			return pool
		elif(replicated_pool):
			replicated_pool.add_slave(pool)
		else:
			replicated_pool = ReplicatedConnectionPool(pool)
	
	return replicated_pool

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

class ReplicatedConnectionPool(object):
	"""
	A collection of database servers in a replicated environment.
	
	Queries are examined to see if there are SELECTs, with all
	reads being sent to the slaves in round-robin mode, and all
	writes are sent to the master.
	
	When write_only_master is True, the master server is not
	used for reads. Otherwise it is included in the round-robin
	of servers to read from.
	
	If there are no slaves, all queries are sent to the master.
	"""
	def __init__(self, master, write_only_master=False):
		"""
		Set up a replicated DB connection.
		
		Given an initial master server, initialize a deque to be
		used to store slaves and select them via round-robin.
		"""
		self.master = master
		self.slaves = collections.deque()
		if not(write_only_master):
			self.slaves.append(self.master)
	
	def add_slave(self, pool):
		"""
		Add a ConnectionPool as a slave.
		"""
		if(pool not in self.slaves):
			self.slaves.append(pool)
	
	def runOperation(self, query, *args, **kwargs):
		"""
		Run an operation on the master.
		
		Note that even though 'operations' (e.g., inserts, deletes, updates)
		should always be on the master, we still check the query, since
		it could just be a programming error.
		"""
		pool = self.get_pool_for(query)
		pool.runOperation(query, *args, **kwargs)
	
	def runQuery(self, query, *args, **kwargs):
		"""
		Run a query on a slave.
		
		Note that even though 'queries' (e.g., selects) should always be on 
		a slave, we still check the query, since it could just be a programming error.
		"""
		pool = self.get_pool_for(query)
		return pool.runQuery(query, *args, **kwargs)
	
	def runInteraction(self, interaction, *args, **kwargs):
		"""
		Run an interaction on the master.
		"""
		self.master.runInteraction(interaction, *args, **kwargs)
	
	def runWithConnection(self, func, *args, **kwargs):
		"""
		Run a function, providing the connection object for the master.
		"""
		self.master.runWithConnection(func, *args, **kwargs)
	
	def get_slave(self):
		"""
		Return the next slave in the round robin.
		"""
		if not(self.slaves):
			return self.master
		self.slaves.rotate(1)
		return self.slaves[-1]
	
	def get_pool_for(self, query):
		"""
		Return a slave if this is a SELECT query, else return the master.
		"""
		if(query.startswith('SELECT')):
			return self.get_slave()
		else:
			return self.master

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
		return adbapi.ConnectionPool.runOperation(self, *args, **kwargs)
	
	def _runOperation(self, trans, *args, **kw):
		return trans.execute(*args, **kw)
	
	def runQuery(self, *args, **kwargs):
		"""
		Trivial override to provide debugging support.
		"""
		if(debug):
			print args, kwargs
		return adbapi.ConnectionPool.runQuery(self, *args, **kwargs)
	
	def runInteraction(self, interaction, *args, **kw):
		"""
		Run a function, passing it a cursor from this pool.
		
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
			if(result and isinstance(result, (list, tuple)) and isinstance(result[0], (list, tuple))):
				result = [dict(zip([c[0] for c in trans._cursor.description], item)) for item in result]
			trans.close()
			conn.commit()
			return result
		except:
			conn.rollback()
			raise
	
	def _runWithConnection(self, func, *args, **kw):
		conn = self.connectionFactory(self)
		try:
			result = func(conn, *args, **kw)
			conn.commit()
			return result
		except:
			excType, excValue, excTraceback = sys.exc_info()
			try:
				conn.rollback()
			except:
				log.err(None, "Rollback failed")
			raise excType, excValue, excTraceback
