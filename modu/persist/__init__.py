# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, warnings
from MySQLdb import cursors, converters

from modu.persist import storable

DEFAULT_STORE_NAME = '__default__'

def build_insert(table, data):
	"""
	Given a table name and a dictionary, construct an INSERT query. Keys are
	sorted alphabetically before output, so the result of running a semantically
	identical dictionary should be the same every time.
	
	Use modu.persist.RAW to embed SQL directly in the VALUES clause.
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
	sorted alphabetically before output, so the result of running a semantically
	identical dictionary should be the same every time. For more info, see the
	build_where() docstring.
	
	These SELECTs always select * from a single table.
	
	Special keys can be inserted in the provided dictionary, such that:
		'__select_keyword'	  is inserted between 'SELECT' and '*'
	
	"""
	if('__select_keyword' in data):
		query = "SELECT %s * FROM `%s` " % (data['__select_keyword'], table)
	else:
		query = "SELECT * FROM `%s` " % table
	
	return query + build_where(data)
	
def build_where(data):
	"""
	Given a dictionary, construct a WHERE clause. Keys are sorted alphabetically
	before output, so the result of running a semantically identical dictionary
	should be the same every time.
	
	Special keys can be inserted in the provided dictionary, such that:
		'__order_by'		  inserts an ORDER BY clause. ASC/DESC must be
							  part of the string if you wish to use them
		'__limit'			  add a LIMIT clause to this query
	
	Additionally, certain types of values have alternate output:
		list/tuple types	  result in an IN statement
		None				  results in an ISNULL statement
		persist.RAW objects	  result in directly embedded SQL, such that
							  'col1':RAW(" = ENCRYPT('whatever')") equals
							  `col1` = ENCRYPT('whatever')
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
	"""
	conv_dict = converters.conversions.copy()
	# This is only used in build_replace/insert()
	conv_dict[RAW] = Raw2Literal
	return query % MySQLdb.escape_sequence(args, conv_dict)

class NOT:
	"""
	Allows NOTs to be embedded in constructed queries.
	"""
	def __init__(self, value):
		self.value = value

class RAW:
	"""
	Allows RAW SQL to be embedded in constructed queries.
	"""
	def __init__(self, value):
		self.value = value

class LIKE(RAW):
	"""
	Allows LIKE statement to be embedded in constructed queries.
	This might not be so safe to use, since it doesn't do any
	escaping of the match string.
	
	The same problem exists with RAW, but at least there it
	should be obvious that the ball is in your court.
	"""
	def __init__(self, match):
		# This is a tricky one. These strings always go through an
		# interpolation process, so we have to double up on the %
		self.value = " LIKE '%%" + match + "%%'"

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
	"""
	
	@classmethod
	def get_store(cls, name=DEFAULT_STORE_NAME):
		"""
		Return the current Store instance, if it exists.
		"""
		if(hasattr(cls, '_stores')):
			if(name in cls._stores):
				return cls._stores[name]
		return None

	def __init__(self, connection, debug_file=None, name=DEFAULT_STORE_NAME):
		"""
		Create a Store for a given DB connection object.
		
		Registered factories can choose whether or not to use GUIDs.
		
		If you choose not to use GUIDs (say, by having each DB table contain an
		auto_increment ID column), each INSERT (but not REPLACE, aka update) will
		LOCK the table, execute the INSERT, read the MAX(id) for that table, and
		finally UNLOCK the table.
		"""
		self.connection = connection
		self.cache = False
		self.debug_file = debug_file
		
		self._factories = {}
		self._object_cache = {}
		
		if not(hasattr(Store, '_stores')):
			Store._stores = {}
		elif(name in Store._stores):
			raise RuntimeError("There is already a Store instance by the name '%s'." % name)
		Store._stores[name] = self
	
	def get_cursor(self, cursor_type=cursors.SSDictCursor):
		"""
		To run queries directly against the Store's DB connection,
		get a cursor object from this function. The default cursor
		type is SSDictCursor, but others may be passed in as an
		optional parameter.
		"""
		if(cursor_type):
			cur = self.connection.cursor(cursor_type)
		else:
			cur = self.connection.cursor()
		return cur
	
	def register_factory(self, table, factory):
		"""
		Register an object to be the factory for this class.
		"""
		if not(storable.IFactory.providedBy(factory)):
			raise ValueError('%r does not implement IFactory' % factory)
		self._factories[table] = factory
		factory.set_store(self)
	
	def has_factory(self, table):
		return table in self._factories
	
	def get_factory(self, table):
		if(table not in self._factories):
			raise KeyError('There is no factory registered for the table `%s`' % table)
		return self._factories[table]
	
	def ensure_factory(self, table, *args, **kwargs):
		if(table not in self._factories):
			self.register_factory(table, storable.DefaultFactory(table, *args, **kwargs))
	
	def fetch_id(self, storable):
		"""
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
	
	def load(self, table, data, ignore_cache=False):
		if(table not in self._factories):
			raise NotImplementedError('There is no factory registered for the table `%s`' % table)
		
		factory = self._factories[table]
		if(isinstance(data, basestring)):
			query = data
		else:
			query = factory.create_item_query(data)
		
		if(query in self._object_cache and self.cache and not ignore_cache):
			return self._object_cache[query]
		
		self.log(query)
		
		result = factory.get_items_by_query(query)
		
		if(callable(result)):
			return result()
		
		if(self.cache):
			self._object_cache[query] = result
		
		return result
	
	def load_one(self, table, data, ignore_cache=False):
		results = self.load(table, data, ignore_cache)
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
			assert(child_id not in id_list or not factory.uses_guids(), 'Found circular storable reference during save')
			_save(child)
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
				cur.execute('SELECT MAX(%s) AS id FROM `%s`' % (factory.get_primary_key(), table))
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
					_destroy(child)
					child_list.extend(child.get_related_storables())
					id_list.append(child_id)
	
	def _destroy(self, storable_item):
		delete_query = "DELETE FROM `%s` WHERE id = %%s" % storable_item.get_table()
		cur = self.get_cursor(None)
		
		query = interp(delete_query, [storable_item.get_id()])
		
		self.log(query)
			
		cur.execute(query)
		storable_item.reset_id()
	
	def log(self, message):
		if(self.debug_file):
			self.debug_file.write("[Store] %s\n" % message)

