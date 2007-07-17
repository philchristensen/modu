# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
The modu.persist package is home to modu's database abstraction
layer and object/relational mapping API.

@var DEFAULT_STORE_NAME: the default Store name
@type DEFAULT_STORE_NAME: str
"""

from __future__ import generators

import MySQLdb, warnings
from MySQLdb import cursors, converters

from modu.persist import storable

DEFAULT_STORE_NAME = '__default__'

def build_insert(table, data):
	"""
	Given a table name and a dictionary, construct an INSERT query. Keys are
	sorted alphabetically before output, so the result of passing a semantically
	identical dictionary should be the same every time.
	
	Use modu.persist.RAW to embed SQL directly in the VALUES clause.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	"""
	keys = data.keys()
	keys.sort()
	values = [data[key] for key in keys]
	query = 'INSERT INTO `%s` (`%s`) VALUES (%s)' % (table, '`, `'.join(keys), ', '.join(['%s'] * len(data)))
	return interp(query, values)


def build_replace(table, data):
	"""
	Given a table name and a dictionary, construct an REPLACE INTO query. Keys are
	sorted alphabetically before output, so the result of running a semantically
	identical dictionary should be the same every time.
	
	Use modu.persist.RAW to embed SQL directly in the SET clause.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	"""
	keys = data.keys()
	keys.sort()
	values = [data[key] for key in keys]
	query = 'REPLACE INTO `%s` SET ' % table
	query += ', '.join(['`%s` = %%s'] * len(data)) % tuple(keys)
	return interp(query, values)


def build_select(table, data):
	"""
	Given a table name and a dictionary, construct an SELECT query. Keys are
	sorted alphabetically before output, so the result of passing a semantically
	identical dictionary should be the same every time.
	
	These SELECTs always select * from a single table.
	
	Special keys can be inserted in the provided dictionary, such that:
	
		- B{__select_keyword}:	is inserted between 'SELECT' and '*'
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	
	@seealso: L{build_where()}
	"""
	if('__select_keyword' in data):
		query = "SELECT %s * FROM `%s` " % (data['__select_keyword'], table)
	else:
		query = "SELECT * FROM `%s` " % table
	
	return query + build_where(data)


def build_where(data):
	"""
	Given a dictionary, construct a WHERE clause. Keys are sorted alphabetically
	before output, so the result of passing a semantically identical dictionary
	should be the same every time.
	
	Special keys can be inserted in the provided dictionary, such that:
	
		- B{__order_by}:	inserts an ORDER BY clause. ASC/DESC must be
							part of the string if you wish to use them
		- B{__limit}:		add a LIMIT clause to this query
	
	Additionally, certain types of values have alternate output:
	
		- B{list/tuple types}:		result in an IN statement
		- B{None}					results in an ISNULL statement
		- B{persist.RAW objects}:	result in directly embedded SQL, such that
									C{'col1':RAW(" = ENCRYPT('whatever')")} equals
									C{`col1` = ENCRYPT('whatever')}
		- B{persist.NOT objects}:	result in a NOT statement
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL fragment
	@rtype: str
	"""
	query = ''
	criteria = []
	values = []
	keys = data.keys()
	keys.sort()
	for key in keys:
		if(key.startswith('_')):
			continue
		value = data[key]
		if(isinstance(value, list) or isinstance(value, tuple)):
			criteria.append('`%s` IN (%s)' % (key, ', '.join(['%s'] * len(value))))
			values.extend(value)
		elif(isinstance(value, RAW)):
			criteria.append('`%s`%s' % (key, value.value))
		elif(value is None):
			criteria.append('ISNULL(`%s`)' % key)
		elif(isinstance(value, NOT)):
			criteria.append('`%s` <> %%s' % key)
			values.append(value.value)
		else:
			criteria.append('`%s` = %%s' % key)
			values.append(value)
	
	if(criteria):
		query += 'WHERE '
		query += ' AND '.join(criteria)
	if('__order_by' in data):
		query += ' ORDER BY %s' % data['__order_by']
	if('__limit' in data):
		query += ' LIMIT %s' % data['__limit']
	
	return interp(query, values)


def interp(query, args):
	"""
	Interpolate the provided arguments into the provided query, using
	the DB-API's default conversions, with the additional 'RAW' support
	from modu.persist.Raw2Literal
	
	@param query: A query string with placeholders
	@type query: str
	
	@param args: A list of query values
	@type args: sequence
	
	@returns: an interpolated SQL query
	@rtype: str
	"""
	conv_dict = converters.conversions.copy()
	# This is only used in build_replace/insert()
	conv_dict[RAW] = Raw2Literal
	return query % MySQLdb.escape_sequence(args, conv_dict)


class NOT:
	"""
	Allows NOTs to be embedded in constructed queries.
	
	@ivar value: The value to NOT be
	"""
	def __init__(self, value):
		self.value = value


class RAW:
	"""
	Allows RAW SQL to be embedded in constructed queries.
	
	@ivar value: "Raw" (i.e., properly escaped) SQL
	"""
	def __init__(self, value):
		self.value = value


def Raw2Literal(o, d):
	"""
	Provides conversion support for RAW
	"""
	return o.value


class Store(object):
	"""
	persist.Store is the routing point for most interactions with the Storable
	persistence layer. You create a single Store object for any given runtime,
	and load any desired objects through this interface, after registering
	factories for each table you wish to load objects from.
	
	@cvar _stores: pool of Store objects
	@type _stores: dict
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
		if(hasattr(cls, '_stores')):
			if(name in cls._stores):
				return cls._stores[name]
		return None

	def __init__(self, connection, name=DEFAULT_STORE_NAME):
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
		self.connection = connection
		self.debug_file = None
		
		self._factories = {}
		
		if(name in self._stores):
			raise RuntimeError("There is already a Store instance by the name '%s'." % name)
		self._stores[name] = self
	
	def get_cursor(self, cursor_type=cursors.SSDictCursor):
		"""
		Get a database cursor.
		
		To run queries directly against the Store's DB connection,
		get a cursor object from this function. The default cursor
		type is SSDictCursor, but others may be passed in as an
		optional parameter.
		
		@param cursor_type: the cursor type to use
		@type cursor_type: valid DB-API cursor
		"""
		if(cursor_type):
			cur = self.connection.cursor(cursor_type)
		else:
			cur = self.connection.cursor()
		return cur
	
	def register_factory(self, table, factory):
		"""
		Register an object to be the factory for this class.
		
		@param table: the table to register the given factory for
		@type table: L{storable.IFactory} implementor
		"""
		if not(storable.IFactory.providedBy(factory)):
			raise ValueError('%r does not implement IFactory' % factory)
		self._factories[table] = factory
		factory.store = self
	
	def has_factory(self, table):
		"""
		Does this store already know how to handle the provided table?
		"""
		return table in self._factories
	
	def get_factory(self, table):
		"""
		Return the factory registered for the given table.
		"""
		if(table not in self._factories):
			raise KeyError('There is no factory registered for the table `%s`' % table)
		return self._factories[table]
	
	def ensure_factory(self, table, *args, **kwargs):
		"""
		Register a DefaultFactory for the provided table.
		
		A convenience method, if there is already a factory registered,
		and the function was not passed a keyword argument 'force',
		any other args or kwargs are passed to the storable.DefaultFactory
		constructor.
		"""
		if(kwargs.setdefault('force', False) or table not in self._factories):
			del kwargs['force']
			self.register_factory(table, storable.DefaultFactory(table, *args, **kwargs))
	
	def fetch_id(self, storable):
		"""
		Attempt to fetch an ID for this object, if necessary.
		
		"Predict" the id for this storable. If GUIDs are being used,
		this method will fetch a new GUID, set it, and return
		that ID immediately (assuming that this object will ultimately
		be saved with that ID).
		
		If GUIDs are not being used, this method will return 0 if
		this is an unsaved object. It's not possible to use "predictive"
		IDs in that case.
		"""
		id = storable.get_id()
		if(id == 0):
			table = storable.get_table()
			if not(self.has_factory(table)):
				raise NotImplementedError('There is no factory registered for the table `%s`' % table)
			factory = self.get_factory(table)
			new_id = factory.get_id()
			storable.set_id(new_id)
			return new_id
		return id
	
	def load(self, table, data={}, **kwargs):
		"""
		Load an object from the requested table.
		
		This function uses whatever factory is registered for the requested
		table. `data` may be either a dict-like object or a query string
		(which skips the query-building phase of the factory).
		
		Any additional keyword arguments are added to the `data` dict,
		and are ignored if `data` is a query string.
		
		Returns an iterable object.
		"""
		if(table not in self._factories):
			raise NotImplementedError('There is no factory registered for the table `%s`' % table)
		
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
			raise RuntimeError('Result of %s::get_items_by_query() does not return an iterable object.', result.__class__.__name__)
		
		if(callable(result)):
			return result()
		
		return result
	
	def load_one(self, table, data={}, **kwargs):
		"""
		Load one item from the store. If the resulting query returns
		multiple rows/objects, the first is returned, and the rest
		are discarded.
		"""
		results = self.load(table, data, **kwargs)
		for result in list(results):
			return result
		return None
	
	def save(self, storable_item):
		table = storable_item.get_table()
		if(table not in self._factories):
			raise NotImplementedError('There is no factory registered for the table `%s`' % table)
		factory = self._factories[table]
		
		self._save(storable_item, factory)
		child_list = storable_item.get_related_storables()
		id_list = []
		while(child_list):
			child = child_list.pop()
			child_id = self.fetch_id(child)
			child_table = child.get_table()
			if(child_table not in self._factories):
				raise NotImplementedError('There is no factory registered for the table `%s`' % child_table)
			factory = self._factories[child_table]
			assert(child_id not in id_list or not factory.uses_guids(), 'Found circular storable reference during save')
			self._save(child, factory)
			child_list.extend(child.get_related_storables())
			id_list.append(child_id)
	
	def _save(self, storable_item, factory):
		table = storable_item.get_table()
		id = self.fetch_id(storable_item)
		data = storable_item.get_data()
		cur = self.get_cursor()
		
		if(id or factory.uses_guids()):
			data[factory.get_primary_key()] = id
			query = build_replace(table, data)
		else:
			query = build_insert(table, data)
			cur.execute('LOCK TABLES `%s` WRITE' % table)
		
		self.log(query)
		
		cur.execute(query)
		
		if not(factory.uses_guids()):
			if not(storable_item.get_id()):
				cur.execute('SELECT MAX(%s) AS `id` FROM `%s`' % (factory.get_primary_key(), table))
				new_id = cur.fetchone()['id']
				storable_item.set_id(new_id)
				cur.fetchall()
			cur.execute('UNLOCK TABLES')
	
	def destroy(self, storable_item, destroy_related_storables=False):
		self._destroy(storable_item)
		if(destroy_related_storables):
			child_list = storable_item.get_related_storables()
			id_list = []
			while(child_list):
				child = child_list.pop()
				child_id = self.fetch_id(child)
				if(child_id not in id_list):
					self._destroy(child)
					child_list.extend(child.get_related_storables())
					id_list.append(child_id)
	
	def _destroy(self, storable_item):
		delete_query = "DELETE FROM `%s` WHERE `id` = %%s" % storable_item.get_table()
		cur = self.get_cursor(None)
		
		query = interp(delete_query, [storable_item.get_id()])
		
		self.log(query)
		
		cur.execute(query)
		storable_item.reset_id()
	
	def log(self, message):
		if(self.debug_file):
			self.debug_file.write("[Store] %s\n" % message)

