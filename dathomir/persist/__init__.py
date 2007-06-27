# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb, warnings
from MySQLdb import cursors, converters

from dathomir.persist import storable

_current_store = None

def get_store():
	"""
	Return the current Store instance, if it exists.
	"""
	global _current_store
	return _current_store

def build_insert(table, data):
	"""
	Given a table name and a dictionary, construct an INSERT query. Keys are
	sorted alphabetically before output, so the result of running a semantically
	identical dictionary should be the same every time.
	
	Use dathomir.persist.RAW to embed SQL directly in the VALUES clause.
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
	
	Use dathomir.persist.RAW to embed SQL directly in the SET clause.
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
	identical dictionary should be the same every time.
	
	These SELECTs always select * from a single table.
	
	Special keys can be inserted in the provided dictionary, such that:
		'__select_keyword'	  is inserted between 'SELECT' and '*'
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
	if('__select_keyword' in data):
		query = "SELECT %s * FROM `%s` " % (data['__select_keyword'], table)
	else:
		query = "SELECT * FROM `%s` " % table
	
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
			criteria.append('`%s`%s' % (key, value.sql))
		elif(value is None):
			criteria.append('ISNULL(`%s`)' % key)
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
	from dathomir.persist.Raw2Literal
	"""
	conv_dict = converters.conversions.copy()
	conv_dict[RAW] = Raw2Literal
	return query % MySQLdb.escape_sequence(args, conv_dict)

class RAW:
	"""
	Allows RAW SQL to be embedded in constructed queries.
	"""
	def __init__(self, sql):
		self.sql = sql

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
		self.sql = " LIKE '%%" + match + "%%'"

def Raw2Literal(o, d):
	"""
	Provides conversion support for RAW
	"""
	return o.sql

class Store(object):
	"""
	persist.Store is the routing point for most interactions with the Storable
	persistence layer. You create a single Store object for any given runtime,
	and load any desired objects through this interface, after registering
	factories for each table you wish to load objects from.
	"""
	
	def __init__(self, connection, guid_table='guid', debug_file=None):
		"""
		Create a Store. Parameters are mostly identical to the DB-API connect()
		function, but you may also pass in the 'guid_table' parameter, to set
		the name of your GUID table.
		
		If you pass a None value for the 'guid_table' paramter, GUID support is
		disabled.
		
		If you choose not to use GUIDs (say, by having each DB table contain an
		auto_increment ID column), each INSERT (but not REPLACE, aka update) will
		LOCK the table, execute the INSERT, read the MAX(id) for that table, and
		finally UNLOCK the table.
		"""
		self.connection = connection
		
		self._guid_table = guid_table
		self._factories = {}
		self._object_cache = {}
		self.cache = False
		self.debug_file = debug_file
		
		global _current_store
		if(_current_store):
			raise RuntimeError("Only one Store instance may be created.")
		_current_store = self
	
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
	
	def get_guid(self, increment=1):
		"""
		Get a new GUID. If you pass the optional increment parameter, the next
		GUID returned by this function will be that much higher, allowing multi-
		master code to request ranges of IDs in advance, or for efficiency.
		
		If GUIDs are disabled for this Store, return None.
		"""
		if not(self.uses_guids()):
			return None
		
		cur = self.get_cursor()
		
		result = cur.execute('LOCK TABLES `%s` WRITE' % self._guid_table)
		result = cur.execute('SELECT `guid` FROM `%s`' % self._guid_table)
		
		guid = cur.fetchall()[0]['guid']
		
		result = cur.execute('UPDATE `%s` SET `guid` = %%s' % self._guid_table, [guid + increment])
		result = cur.execute('UNLOCK TABLES')
		
		return guid
	
	def uses_guids(self):
		"""
		Does this Store use GUIDs?
		"""
		return self._guid_table != None
	
	def register_factory(self, table, factory):
		"""
		Register an object to be the factory for this class.
		"""
		if not(isinstance(factory, storable.Factory)):
			raise ValueError('%r is not a Factory subclass' % factory)
		self._factories[table] = factory
	
	def has_factory(self, table):
		return table in self._factories
	
	def ensure_factory(self, table, model_class=storable.Storable):
		if(table not in self._factories):
			self.register_factory(table, storable.DefaultFactory(table, model_class))
	
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
		
		if(self.debug_file):
			self.debug_file.write("[Store] %s\n" % query)
		
		result = factory.get_items_by_query(query)
		
		if(self.cache):
			self._object_cache[query] = result
		
		return result
	
	def load_one(self, table, data, ignore_cache=False):
		result = self.load(table, data, ignore_cache)
		if(result and len(result)):
			return result[0]
		return None
	
	def save(self, storable_item):
		self._save(storable_item)
		child_list = storable_item.get_related_storables()
		id_list = []
		while(child_list):
			child = child_list.pop()
			child_id = child.get_id(True)
			assert(child_id not in id_list or not self.uses_guids(), 'Found circular storable reference during save')
			_save(child)
			child_list.extend(child.get_related_storables())
			id_list.append(child_id)
	
	def _save(self, storable_item):
		table = storable_item.get_table()
		id = storable_item.get_id(True)
		data = storable_item.get_data()
		cur = self.get_cursor()
		
		if(id or self.uses_guids()):
			data[storable.ID_COLUMN] = id
			query = build_replace(table, data)
		else:
			query = build_insert(table, data)
			cur.execute('LOCK TABLES `%s` WRITE' % table)
		
		if(self.debug_file):
			self.debug_file.write("[Store] %s\n" % query)
			
		cur.execute(query)
		
		if not(self.uses_guids()):
			cur.execute('SELECT MAX(%s) AS id FROM `%s`' % (storable.ID_COLUMN, table))
			if not(storable_item.get_id()):
				storable_item.set_id(cur.fetchone()['id'])
			cur.fetchall()
			cur.execute('UNLOCK TABLES')
	
	def destroy(self, storable_item, destroy_related_storables=False):
		self._destroy(storable_item)
		if(destroy_related_storables):
			child_list = storable_item.get_related_storables()
			id_list = []
			while(child_list):
				child = child_list.pop()
				child_id = child.get_id(True)
				if(child_id not in id_list):
					_destroy(child)
					child_list.extend(child.get_related_storables())
					id_list.append(child_id)
	
	def _destroy(self, storable_item):
		delete_query = "DELETE FROM `%s` WHERE id = %%s" % storable_item.get_table()
		cur = self.get_cursor(None)
		
		query = interp(delete_query, [storable_item.get_id()])
		
		if(self.debug_file):
			self.debug_file.write("[Store] %s\n" % query)
			
		cur.execute(query)
		storable_item.reset_id()

