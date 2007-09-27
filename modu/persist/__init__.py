# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Home to modu's database abstraction layer and object/relational mapping API.

@var DEFAULT_STORE_NAME: the default Store name
@type DEFAULT_STORE_NAME: str
"""

from modu.persist import storable, sql
import thread, types

DEFAULT_STORE_NAME = '__default__'

def activate_store(req):
	"""
	Examine the req object and its internal modu.app object,
	and create or fetch a store instance to be used by this request.
	"""
	store = Store.get_store()
	if not(store):
		store = Store(req.pool)
	if(req.app.debug_store):
		debug_file = req['wsgi.errors']
	else:
		debug_file = None
	store.debug_file = debug_file
	req['modu.store'] = store


class Store(object):
	"""
	persist.Store is the routing point for most interactions with the Storable
	persistence layer. You create a single Store object for any given thread,
	and load any desired objects through this interface, after registering
	factories for each table you wish to load objects from.
	
	@cvar _stores: pool of Store objects
	@type _stores: dict
	
	@ivar connection: the connection object
	@type connection: a DB-API 2.0 compliant connection
	
	@ivar debug_file: print debug info to this object, if not None
	@type debug_file: a file-like object
	
	@ivar _factories: table names mapped to registered factories
	@type _factories: dict
	"""
	
	_stores = {}
	
	@classmethod
	def get_store(cls, name=DEFAULT_STORE_NAME):
		"""
		Return the current Store instance of the given name, if it exists.
		
		@param name: the name of the Store instance to retrieve
		@type name: str
		
		@returns: requested Store, or None
		"""
		
		name += '-%d' % thread.get_ident()
		
		if(hasattr(cls, '_stores')):
			if(name in cls._stores):
				return cls._stores[name]
		return None
	
	def __init__(self, pool, name=DEFAULT_STORE_NAME):
		"""
		Create a Store for a given DB connection object.
		
		Registered factories can choose whether or not to use GUIDs.
		
		If you choose not to use GUIDs (say, by having each DB table contain an
		auto_increment ID column), each INSERT (but not REPLACE, aka update) will
		LOCK the table, execute the INSERT, read the MAX(id) for that table, and
		finally UNLOCK the table.
		
		@param connection: the connection object to use for this store
		@type connection: a DB-API 2.0 compliant connection (MySQLdb only, for now)
		
		@param name: the name of the Store instance to be created
		@type name: str
		
		@raises RuntimeError: if a Store instance by that name already exists
		"""
		self.pool = pool
		self.debug_file = None
		
		self._factories = {}
		
		name += '-%d' % thread.get_ident()
		if(name in self._stores):
			raise RuntimeError("There is already a Store instance by the name '%s'." % name)
		self._stores[name] = self
	
	def register_factory(self, table, factory):
		"""
		Register an object to be the factory for this class.
		
		@param table: the table to register the given factory for
		@type table: str
		
		@param factory: the factory object to register
		@type factory: L{storable.IFactory} implementor
		
		@raises ValueError: if the provided factory is not a L{storable.IFactory} implementor
		"""
		if not(storable.IFactory.providedBy(factory)):
			raise ValueError('%r does not implement IFactory' % factory)
		self._factories[table] = factory
		factory.store = self
	
	def has_factory(self, table):
		"""
		Does this store already know how to handle the provided table?
		
		@param table: the table whose factory is sought
		
		@returns: boolean
		"""
		return table in self._factories
	
	def get_factory(self, table):
		"""
		Return the factory registered for the given table.
		
		@param table: the table whose factory is sought
		
		@returns: the requested factory
		@rtype: L{storable.IFactory}
		@raises LookupError: if no factory has been registered for the given table
		"""
		if(table not in self._factories):
			raise LookupError('There is no factory registered for the table `%s`' % table)
		return self._factories[table]
	
	def ensure_factory(self, table, *args, **kwargs):
		"""
		Register a DefaultFactory for the provided table.
		
		A convenience method, if there is already a factory registered,
		and the function was not passed a keyword argument 'force',
		any other args or kwargs are passed to the storable.DefaultFactory
		constructor.
		
		@param table: the table to register the given factory for
		@type table: str
		
		@param force: should this override existing factory registrations?
		@type force: bool
		"""
		if(kwargs.setdefault('force', False) or table not in self._factories):
			del kwargs['force']
			self.register_factory(table, storable.DefaultFactory(table, *args, **kwargs))
	
	def fetch_id(self, storable):
		"""
		Fetch an ID for this object, if possible.
		
		"Predict" the id for this storable. If GUIDs are being used,
		this method will fetch a new GUID, set it, and return
		that ID immediately (assuming that this object will ultimately
		be saved with that ID).
		
		If GUIDs are not being used, this method will return 0 if
		this is an unsaved object. It's not possible to use "predictive"
		IDs in that case.
		
		@param storable: the object whose ID you wish to fetch
		@type storable: L{storable.Storable}
		
		@returns: the item's id, or 0
		@rtype: int
		@raises LookupError: if no factory has been registered for this Storable's table
		"""
		id = storable.get_id()
		if(id == 0):
			table = storable.get_table()
			if not(self.has_factory(table)):
				raise LookupError('There is no factory registered for the table `%s`' % table)
			factory = self.get_factory(table)
			new_id = factory.get_id()
			storable.set_id(new_id)
			return new_id
		return id
	
	def load(self, table, data=None, **kwargs):
		"""
		Load an object from the requested table.
		
		This function uses whatever factory is registered for the requested
		table. `data` may be either a dict-like object or a query string
		(which skips the query-building phase of the factory).
		
		Any additional keyword arguments are added to the `data` dict,
		and are ignored if `data` is a query string.
		
		Returns an iterable object.
		
		@param table: the table to register the given factory for
		@type table: str
		
		@param data: a column name to value map; possibly other Factory-specific values
		@type data: dict
		
		@returns: a set of resulting objects
		@rtype: iterable
		@raises LookupError: if no factory has been registered for this Storable's table
		"""
		if(data is None):
			data = kwargs
		elif(isinstance(data, dict)):
			data.update(kwargs)
		
		if(table not in self._factories):
			raise LookupError('There is no factory registered for the table `%s`' % table)
		
		factory = self._factories[table]
		if(isinstance(data, basestring)):
			query = data
		else:
			data.update(kwargs)
			query = factory.create_item_query(data)
		
		result = factory.get_items_by_query(query)
		try:
			iter(result)
		except TypeError:
			raise AssertionError('Result of %s::get_items_by_query() does not return an iterable object.', result.__class__.__name__)
		
		if(callable(result)):
			return result()
		
		return result
	
	def load_one(self, table, data=None, **kwargs):
		"""
		Load one item from the store.
		
		If the resulting query returns multiple rows/objects, the first is
		returned, and the rest are discarded.
		
		@seealso: L{load()}
		"""
		results = self.load(table, data, **kwargs)
		for result in list(results):
			return result
		return None
	
	def save(self, storable, save_related_storables=True):
		"""
		Save the provided Storable.
		
		@param storable: the object you wish to save
		@type storable: L{storable.Storable}
		
		@param save_related_storables: should the items returned by
			L{Storable.get_related_storables()} be automatically saved?
		@type save_related_storables: bool
		
		@raises LookupError: if no factory has been registered for this Storable's table
		"""
		table = storable.get_table()
		if(table not in self._factories):
			raise LookupError('There is no factory registered for the table `%s`' % table)
		factory = self._factories[table]
		
		self._save(storable, factory)
		child_list = storable.get_related_storables()
		id_list = []
		while(child_list and save_related_storables):
			child = child_list.pop()
			child_id = self.fetch_id(child)
			child_table = child.get_table()
			if(child_table not in self._factories):
				raise LookupError('There is no factory registered for the table `%s`' % child_table)
			factory = self._factories[child_table]
			if(child_id in id_list and factory.uses_guids()):
				raise AssertionError('Found circular storable reference during save')
			self._save(child, factory)
			child_list.extend(child.get_related_storables())
			id_list.append(child_id)
	
	def _save(self, storable, factory):
		"""
		Internal function that is responsible for doing the
		actual saving.
		"""
		table = storable.get_table()
		id = self.fetch_id(storable)
		data = storable.get_data()
		
		if(id or factory.uses_guids()):
			data[factory.get_primary_key()] = id
			query = sql.build_replace(table, data)
		else:
			query = sql.build_insert(table, data)
			self.pool.runOperation('LOCK TABLES `%s` WRITE' % table)
	
		self.log(query)
	
		self.pool.runOperation(query)
	
		if not(factory.uses_guids()):
			if not(storable.get_id()):
				rows = self.pool.runQuery('SELECT MAX(%s) AS `id` FROM `%s`' % (factory.get_primary_key(), table))
				new_id = rows[0]['id']
				storable.set_id(new_id)
				#cur.fetchall()
			self.pool.runOperation('UNLOCK TABLES')
		
		storable.set_factory(factory)
	
	def destroy(self, storable, destroy_related_storables=False):
		"""
		Destroy the provided Storable.
		
		@param storable: the object you wish to destroy
		@type storable: L{storable.Storable}
		
		@param destroy_related_storables: should the items returned by
			L{Storable.get_related_storables()} be automatically destroyed?
		@type destroy_related_storables: bool
		"""
		self._destroy(storable)
		child_list = storable.get_related_storables()
		id_list = []
		while(child_list and destroy_related_storables):
			child = child_list.pop()
			child_id = self.fetch_id(child)
			if(child_id in id_list and factory.uses_guids()):
				raise AssertionError('Found circular storable reference during save')
			self._destroy(child)
			child_list.extend(child.get_related_storables())
			id_list.append(child_id)
	
	def _destroy(self, storable):
		"""
		Internal function that is responsible for doing the
		actual destruction.
		"""
		delete_query = sql.build_delete(storable.get_table(), {'id':storable.get_id()})

		self.pool.runOperation(delete_query)
		storable.reset_id()
	
	def log(self, message):
		"""
		I think I might switch to using the Twisted logger, but for
		now this logs output if the debug_file attribute has been set.
		"""
		if(self.debug_file):
			self.debug_file.write("[Store] %s\n" % message)

