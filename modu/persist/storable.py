# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import time, copy

from zope import interface
from zope.interface import implements

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
	def __init__(self, table):
		"""
		When creating a new (unsaved) Storable object, you'll need to
		pass the table name to the object constructor. Subclasses can
		of course provide this automatically -- it is important that
		subclasses call the superclass constructor, though.
		"""
		object.__setattr__(self, '_id', 0)
		object.__setattr__(self, '_dirty', True)
		object.__setattr__(self, '_data', {})
		object.__setattr__(self, '_table', None)
		object.__setattr__(self, 'created_date', 0)
		object.__setattr__(self, 'modified_date', 0)
	
		object.__setattr__(self, '_table', table)
	
	def __setattr__(self, key, value):
		"""
		Whenever the data for this object is updated, a number of 
		bookkeeping variables are updated.
		
		All other attributes are assumed to be SQL column names,
		and therefore must not begin with an underscore.
		"""
		_dict = object.__getattribute__(self, '__dict__')
		if(key not in _dict):
			self.touch()
			object.__getattribute__(self, '_data')[key] = value
		elif not(key.startswith('_')):
			object.__setattr__(self, key, value)
	
	def __getattribute__(self, key):
		"""
		All attributes set must be valid SQL column names. If the
		column does not exist in the chosen table, errors will
		occur on save.
		"""
		if not(key.startswith('_')):
			try:
				func = object.__getattribute__(self, key)
				if(callable(func)):
					return func
			except:
				_data = object.__getattribute__(self, '_data')
				if(key in _data):
					return _data[key]
				_dict = object.__getattribute__(self, '__dict__')
				if(key in _dict):
					return _dict[key]
			
		raise AttributeError('No such attribute "%s" on %r' % (key, self))
	
	def set_id(self, id):
		"""
		Set the ID of this object. This method may only be called once
		in a Storable object's lifetime.
		"""
		if(self.get_id()):
			raise RuntimeError("%r already has the id %d, cannot be set to %d" % (self, self.get_id(), id))
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
		object.__setattr__(self, 'modified_date', time.time())
	
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
	
	def load_data(self, data):
		"""
		This method is called by the Store to populate
		objects with data loaded from the database. `data`
		is assumed to be a hash of column name => value
		pairs, but this is also a convenient way to populate
		or update Storable objects quickly.
		"""
		if('created_date' in data):
			self.created_date = data['created_date']
		else:
			self.created_date = time.time()
		if('modified_date' in data):
			self.modified_date = data['modified_date']
		object.__getattribute__(self, '_data').update(data)
	
	def get_data(self):
		"""
		Return a dict of column name => value pairs. This dict
		will be passed to the query building functions.
		
		If created/modified_date columns were ever populated
		on this object (either from the DB or manually), the
		created/modified_date properties of this object will
		used to update those columns.
		"""
		result = copy.copy(object.__getattribute__(self, '_data'))
		if('created_date' in result):
			result['created_date'] = self.created_date
		if('modified_date' in result):
			result['modified_date'] = self.modified_date
		return result
	
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
	
	def save(self):
		from modu.persist import Store
		store = Store.get_store()
		store.save(self)
	
	def destroy(self):
		from modu.persist import Store
		store = Store.get_store()
		store.destroy(self)

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
	implements(IFactory)
	
	def __init__(self, table=None, model_class=Storable, id_col='id', guid_table='guid'):
		self.table = table
		self.model_class = model_class
		self.id_col = id_col
		self.guid_table = guid_table
	
	def set_store(self, store):
		self.store = store
	
	def get_id(self, increment=1):
		"""
		Get a new GUID. If you pass the optional increment parameter, the next
		GUID returned by this function will be that much higher, allowing multi-
		master code to request ranges of IDs in advance, or for efficiency.
		
		If GUIDs are disabled for this Factory, return None.
		"""
		if not(self.uses_guids()):
			return None
		
		cur = self.store.get_cursor()
		
		result = cur.execute('LOCK TABLES `%s` WRITE' % self.guid_table)
		result = cur.execute('SELECT `guid` FROM `%s`' % self.guid_table)
		
		result = cur.fetchall()
		if(result is None or len(result) == 0):
			guid = 1
			result = cur.execute('INSERT INTO `%s` VALUES (%%s)' % self.guid_table, [guid + increment])
		else:
			guid = result[0]['guid']
			result = cur.execute('UPDATE `%s` SET `guid` = %%s' % self.guid_table, [guid + increment])
		
		result = cur.execute('UNLOCK TABLES')
		
		return guid
	
	def uses_guids(self):
		"""
		Does this Factory use GUIDs?
		"""
		return self.guid_table != None
	
	def get_primary_key(self):
		return self.id_col
	
	def create_item(self, data):
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
		return item
	
	def create_item_query(self, data):
		if not(self.table):
			raise NotImplementedError('%s::create_item_query()' % self.__class__.__name__)
		from modu import persist
		return persist.build_select(self.table, data)
	
	def get_item(self, id):
		(result) = self.get_items({self.id_col:id})
		return result
	
	def get_items(self, data):
		query = self.create_item_query(data)
		return self.get_items_by_query(query)
	
	def get_items_by_query(self, query):
		for record in self.get_item_records(query):
			yield self.create_item(record)
		return
	
	def get_item_records(self, query):
		cursor = self.store.get_cursor()
		cursor.execute(query)
		
		row = cursor.fetchone()
		while(row):
			yield row
			row = cursor.fetchone()
		
		return