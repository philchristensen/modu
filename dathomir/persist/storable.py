#!/usr/bin/env python

# dathomir
# Copyright (C) 1999-2006 Phil Christensen
#
# See LICENSE for details

import time, copy

from dathomir import persist

ID_COLUMN = 'id'

class Storable(object):
	_id = 0
	_dirty = True
	_data = {}
	
	created_date = 0
	modified_date = 0
	
	def __setattr__(self, key, value):
		if(key not in self.__dict__):
			object.__setattr__(self, 'modified_date', time.time())
			object.__setattr__(self, '_dirty', True)
			object.__setattr__(self, 'data', value)
		elif not(key.startswith('_')):
			object.__setattr__(self, key, value)
	
	def __getattribute__(self, key):
		if not(key.startswith('_')):
			_dict = object.__getattribute__(self, '__dict__')
			_data = object.__getattribute__(self, '_data')
			if(key in _dict):
				return _dict[key]
			if(key in _data):
				return _data[key]
			
		raise AttributeError('No such attribute "%s" on %r' % (key, self))
	
	def set_id(self, id):
		if(self.get_id()):
			raise RuntimeError("%r already has the id %d, cannot be set to %d" % (self, self.get_id(), id))
		object.__setattr__(self, '_id', id)
	
	def get_id(self):
		return object.__getattribute__(self, '_id')
	
	def touch(self):
		object.__setattr__(self, '_dirty', True)
		self.modified_date = time.time()
	
	def clean(self):
		object.__setattr__(self, '_dirty', False)
	
	def is_dirty(self):
		return object.__getattribute__(self, '_dirty')
	
	def load_data(self, data):
		if(ID_COLUMN in data):
			self.set_id(data[ID_COLUMN])
		if('created_date' in data):
			self.created_date = data['created_date']
		else:
			self.created_date = time.time()
		if('modified_date' in data):
			self.modified_date = data['modified_date']
		object.__setattr__(self, '_data', data)
	
	def get_data(self):
		result = copy.copy(object.__getattribute__(self, '_data'))
		if('created_date' in result):
			result['created_date'] = self.created_date
		if('modified_date' in result):
			result['modified_date'] = self.modified_date
		return result
	
	def get_table(self):
		raise NotImplementedError('%s::get_table()' % self.__class__.__name__)
	
	def get_related_storables(self):
		return []
	
	def destroyed(self):
		object.__setattr__(self, '_id', 0)

class Factory(object):
	def get_item(id):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)
	
	def get_items(attribs):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)
	
	def get_items_by_query(query):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)
	
	def create_item(record):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)
	
	def create_item_query_for_type(attribs, type):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)
	
	def create_item_query(attribs):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)
	
	def get_item_records(query):
		raise NotImplementedError('%s::get_items()' % self.__class__.__name__)

class DefaultFactory(object):
	table = None
	model_class = None
	
	def __init__(self, table=None, model_class=None):
		self.table = table
		self.model_class = model_class
	
	def create_item(self, data):
		if not(self.model_class):
			raise NotImplementedError('%s::create_item()' % self.__class__.__name__)
		
		item = self.model_class()
		item.load_data(data)
		return item
	
	def create_item_query(self, data):
		if not(self.table):
			raise NotImplementedError('%s::create_item_query()' % self.__class__.__name__)
		return self.create_item_query_for_type(self.table, data)
	
	def create_item_query_for_type(self, table, data):
		return persist.build_select(table, data)
	
	def get_item(id):
		(result) = self.get_items({'id':id})
		return result
	
	def get_items(data):
		result = self.create_item_query(data)
		return self.get_items_by_query(*result)
	
	def get_items_by_query(query, values):
		records = self.get_item_records(query, values)
		if(records):
			result = map(lambda(data): create_item(data), records)
		if not(result):
			return False
		return result
	
	def get_item_records(query, values):
		store = persist.get_store()
		store.cursor.execute(query, values)
		return store.cursor.fetchall()