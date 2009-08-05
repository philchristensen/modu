# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Various classes and functions needed to create Storable instances and subclasses.
"""

import time, copy, sys

from zope import interface
from zope.interface import implements, Interface, Attribute
from modu.persist import sql

def cached(timeout):
	"""
	Function decorator to enable caching for singleton functions.
	"""
	def _cached(func):
		func.expires = 0
		def __cached(*args, **kwargs):
			if(timeout and func.expires < time.time() and hasattr(func, 'cache')):
				del func.cache
			if(hasattr(func, 'cache')):
				return func.cache
			result = func(*args, **kwargs)
			if(result):
				func.cache = result
				func.expires = time.time() + timeout
			return result
		return __cached
	try:
		# see if it's an int
		int(timeout)
	except TypeError:
		func = timeout
		timeout = 0
		return _cached(func)
	return _cached

def cachedmethod(timeout):
	"""
	Function decorator to enable caching for instance methods.
	"""
	def _cached(func):
		if not(hasattr(func, 'expires')):
			func.expires = {}
			func.cache = {}
		def __cached(self, *args, **kwargs):
			if(timeout and func.expires.get(repr(self), 0) < time.time()):
				if(repr(self) in func.cache):
					del func.cache[repr(self)]
			if(repr(self) in func.cache):
				return func.cache[repr(self)]
			result = func(self, *args, **kwargs)
			if(result):
				func.cache[repr(self)] = result
				func.expires[repr(self)] = time.time() + timeout
			return result
		return __cached
	try:
		# see if it's an int
		int(timeout)
	except TypeError:
		func = timeout
		timeout = 0
		return _cached(func)
	return _cached

class IStorable(Interface):
	def set_id(self, id):
		"""
		Set the ID/primary key of this item.
		
		Note that this method will normally only be called once,
		so implementors may wish to throw an exception if called
		more then once between calls to C{reset_id()}
		"""
	
	def get_id(self):
		"""
		Get the ID/primary key of this item, if available.
		
		Unsaved objects will return 0.
		"""
	
	def touch(self):
		"""
		Mark this object as 'dirty', i.e., requiring persistence.
		"""
	
	def clean(self):
		"""
		Clean this object, indicating it no longer needs to be saved.
		"""
	
	def is_dirty(self):
		"""
		Return True if this object needs to be saved.
		"""
	
	def set_factory(self, factory):
		"""
		This function will normally only be called by the factory that
		created this item, e.g. storable.set_factory(self).
		"""
	
	def get_factory(self):
		"""
		Return the factory that created this object.
		"""
	
	def get_store(self):
		"""
		Return the store this object came from.
		"""
	
	def reload(self):
		"""
		Reload this object, discarding any unsaved changes.
		"""
	
	def load_data(self, data):
		"""
		Load the provided data into this object in some way.
		"""
	
	def get_data(self):
		"""
		Return the data for this object's record as a dict,
		column name keyed to column value.
		"""
	
	def get_related_storables(self):
		"""
		Return a list of items that should be saved along with
		this object, or deleted along with it.
		"""
	
	def reset_id(self):
		"""
		Reset this object's id to 0, so it will be assigned a new
		ID on save. Useful for cloning objects.
		"""

class Storable(object):
	"""
	A Storable object represents a single standardized result from a
	relational database. The most common scenario is for each row of
	a database to provide the data for a single Storable object, but
	the Storable API allows for creation of custom complex queries
	that can be used for object instantiation as well.
	
	Once loaded via a modu.persist.Store, Storable objects provide
	access to the data of the result through object attribute access.
	
	Although the standard Storable class provides all the functionality
	needed to implement a simple row-based storage metaphor, subclasses
	can override the instantiation process to implement more advanced
	persistence mechanisms.
	"""
	implements(IStorable)
	
	def __init__(self, table):
		"""
		When creating a new (unsaved) Storable object, you'll need to
		pass the table name to the object constructor. Subclasses can
		of course provide this automatically -- it is important that
		subclasses call the superclass constructor, though.
		"""
		object.__setattr__(self, '_id', 0)
		object.__setattr__(self, '_dirty', True)
		object.__setattr__(self, '_new', True)
		object.__setattr__(self, '_data', {})
		object.__setattr__(self, '_table', table)
		object.__setattr__(self, '_factory', None)
	
	def __setitem__(self, key, value):
		if(object.__getattribute__(self, '_data').get(key) != value):
			self.touch()
		object.__getattribute__(self, '_data')[key] = value
	
	def __getitem__(self, key):
		return object.__getattribute__(self, '_data')[key]
	
	def __contains__(self, key):
		return key in object.__getattribute__(self, '_data')
	
	def __len__(self):
		return len(object.__getattribute__(self, '_data'))
	
	def __iter__(self):
		return object.__getattribute__(self, '_data').iterkeys()
	
	def iterkeys(self):
		return object.__getattribute__(self, '_data').iterkeys()
	
	def __cmp__(self, other):
		if not(isinstance(other, Storable)):
			return -1
		
		if(self.get_table() != other.get_table()):
			return 1
		
		if(self.get_data() != other.get_data()):
			return 1
		
		return 0
	
	def __setattr__(self, key, value):
		"""
		Whenever the data for this object is updated, a number of 
		bookkeeping variables are updated.
		
		All other attributes are assumed to be SQL column names,
		unless they begin with an underscore. Undersore-prefixed
		attributes can be used to store non-persistent data.
		"""
		if(key == 'id'):
			return self.set_id(value)
		if(key.startswith('_')):
			_dict = object.__getattribute__(self, '__dict__')
			_dict[key] = value
		else:
			self[key] = value
	
	def __getattribute__(self, key):
		"""
		All attributes set must be valid SQL column names. If the
		column does not exist in the chosen table, errors will
		occur on save.
		"""
		if(key == 'id'):
			return self.get_id()
		try:
			func = object.__getattribute__(self, key)
			if(callable(func)):
				return func
		except:
			pass
		
		_dict = object.__getattribute__(self, '__dict__')
		_data = object.__getattribute__(self, '_data')
		if(key.startswith('_') and key in _dict):
			return _dict[key]
		elif(key in _data):
			return _data[key]
			
		raise AttributeError('No such attribute "%s" on %r' % (key, self))
	
	def is_new(self):
		return object.__getattribute__(self, '_new')
	
	def set_new(self, newness):
		object.__setattr__(self, '_new', newness)
	
	def set_id(self, id, set_old=True):
		"""
		Set the ID of this object. This method may only be called once
		in a Storable object's lifetime.
		"""
		if(self.get_id()):
			raise RuntimeError("%r already has the id %d, cannot be set to %d" % (self, self.get_id(), id))
		if(set_old):
			object.__setattr__(self, '_new', False)
		object.__setattr__(self, '_id', id)
	
	def get_id(self):
		"""
		Get the ID of this object.
		"""
		return object.__getattribute__(self, '_id')
	
	def touch(self):
		"""
		Mark this object as `dirty` and update the last
		modified date.
		"""
		object.__setattr__(self, '_dirty', True)
	
	def clean(self):
		"""
		Make this object as *not* `dirty`
		"""
		object.__setattr__(self, '_dirty', False)
	
	def is_dirty(self):
		"""
		Return the "cleanliness" of this object.
		"""
		return object.__getattribute__(self, '_dirty')
	
	def set_factory(self, factory):
		"""
		Called my this object's factory after load_data()
		"""
		object.__setattr__(self, '_factory', factory)
	
	def get_factory(self):
		"""
		Returns the factory that last loaded or saved this object.
		Newly created, unsaved objects have no factory.
		"""
		return object.__getattribute__(self, '_factory')
	
	def get_store(self):
		"""
		Convenience method to get the store for this object,
		and provide meaningful messages after developer error.
		"""
		factory = object.__getattribute__(self, '_factory')
		if not(factory):
			raise RuntimeError, "New objects do not have factories."
		if not(factory.store):
			raise RuntimeError, "This object's factory has not been registered with a Store."
		return factory.store
		
	def reload(self):
		"""
		Reload this object from the database, discarding any unsaved changes.
		"""
		factory = self.get_factory()
		[current] = factory.get_items(dict(id=self.get_id()))
		self.load_data(current.get_data())
		self.clean()
		
	def load_data(self, data):
		"""
		This method is called by the Store to populate
		objects with data loaded from the database. `data`
		is assumed to be a hash of column name => value
		pairs, but this is also a convenient way to populate
		or update Storable objects quickly.
		"""
		for key, value in data.items():
			self[key] = value
	
	def get_data(self):
		"""
		Return a dict of column name => value pairs. This dict
		will be passed to the query building functions.
		"""
		return copy.copy(object.__getattribute__(self, '_data'))
	
	def get_table(self):
		"""
		Return the table this object will be saved to.
		"""
		return object.__getattribute__(self, '_table')
	
	def get_related_storables(self):
		"""
		Return a list of Storables that may be "related" to
		this object in some way. These items will be saved when
		this object is saved, and destroyed when this item is
		destroyed.
		"""
		return []
	
	def reset_id(self):
		"""
		Use this function with caution (or not at all). It is used
		by the persistence layer to reset an object's ID when it is
		destroyed, but it is also a convenient way to clone objects.
		
		Once an object has no ID, (and marked as dirty) it can be
		resaved, creating a new record.
		"""
		object.__setattr__(self, '_id', 0)

class IFactory(interface.Interface):
	def set_store(self, store):
		"""
		Associate a store with this factory.
		"""
	
	def get_id(self):
		"""
		Generate an ID (if appropriate) for an object about to be saved.
		"""
	
	def get_item(self, id):
		"""
		Load an object based on its ID.
		"""
	
	def get_store(self, id):
		"""
		Get the store this factory is registered with, if possible.
		"""
	
	def get_items(self, attribs):
		"""
		Return an iterable of items that match the provided attributes.
		"""
	
	def get_items_by_query(self, query):
		"""
		Return an iterable of items that are returned by the provided query.
		"""
	
	def create_item(self, record):
		"""
		Create an object for the provided record.
		"""
	
	def create_item_query(self, attribs):
		"""
		Create a query with the provided attributes.
		"""
	
	def get_item_records(self, query):
		"""
		Return an iterable of records returned by the provided query.
		"""

class DefaultFactory(object):
	"""
	The standard object factory for modu. Can build queries and load objects
	for most common scenarios.
	"""
	
	implements(IFactory)
	
	default_cache_setting = False
	
	def __init__(self, table, model_class=Storable, id_col='id', guid_table='guid', use_cache=None):
		self.table = table
		self.model_class = model_class
		self.id_col = id_col
		self.guid_table = guid_table
		self.store = None
		
		if(use_cache is not None):
			self.use_cache = use_cache
		else:
			self.use_cache = self.default_cache_setting
		self.cache = {}
	
	def get_id(self, increment=1):
		"""
		Get a new GUID. If you pass the optional increment parameter, the next
		GUID returned by this function will be that much higher, allowing multi-
		master code to request ranges of IDs in advance, or for efficiency.
		
		If GUIDs are disabled for this Factory, return None.
		"""
		if not(self.uses_guids()):
			return None

		self.store.pool.runOperation('LOCK TABLES `%s` WRITE' % self.guid_table)
		result = self.store.pool.runQuery('SELECT `guid` FROM `%s`' % self.guid_table)
	
		if(result is None or len(result) == 0):
			guid = 1
			self.store.pool.runOperation('INSERT INTO `%s` VALUES (%%s)' % self.guid_table, [guid + increment])
		else:
			guid = result[0]['guid']
			self.store.pool.runOperation('UPDATE `%s` SET `guid` = %%s' % self.guid_table, [guid + increment])
	
		result = self.store.pool.runOperation('UNLOCK TABLES')

		return guid
	
	def uses_guids(self):
		"""
		Does this Factory use GUIDs?
		"""
		return self.guid_table != None
	
	def get_primary_key(self):
		"""
		Return the name of the column that will contain IDs
		for objects created by this factory.
		"""
		return self.id_col
	
	def create_item(self, data):
		"""
		Create an object of some kind from the provided data/record.
		"""
		if not(self.model_class and self.table):
			raise NotImplementedError('%s::create_item()' % self.__class__.__name__)
		if(self.model_class is Storable):
			item = self.model_class(self.table)
		else:
			item = self.model_class()
		
		if(self.id_col in data):
			item.set_id(data[self.id_col])
			del data[self.id_col]
		
		item.load_data(data)
		item.set_factory(self)
		item.set_new(False)
		item.clean()
		return item
	
	def create_item_query(self, data):
		"""
		Given `data` as a dict of column => value constraints,
		create a query that will load some object(s). 
		"""
		if not(self.table):
			raise NotImplementedError('%s::create_item_query()' % self.__class__.__name__)
		from modu import persist
		return sql.build_select(self.table, data)
	
	def get_item(self, id):
		"""
		Load an item directly via its primary key.
		"""
		(result) = self.get_items({self.id_col:id})
		return result
	
	def get_items(self, data):
		"""
		Given a dict of column => value constraints, load any
		objects that are returned from the database.
		"""
		query = self.create_item_query(data)
		return self.get_items_by_query(query)
	
	def get_items_by_query(self, query):
		"""
		Given the provided query, attempt to load each result row
		as an object created by this factory.
		"""
		if(query not in self.cache):
			result = [self.create_item(record)
						for record in self.get_item_records(query) or []]
			if(result and self.use_cache):
				self.cache[query] = result
			else:
				return result
		return self.cache[query]
	
	def get_item_records(self, query):
		"""
		Query the database and return all the results.
		"""
		self.store.log(query)
		return self.store.pool.runQuery(query)
