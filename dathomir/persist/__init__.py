_current_store = None

import MySQLdb
from MySQLdb import cursors

from dathomir.persist import storable

def get_store():
	global _current_store
	return _current_store

def build_insert(table, data):
	cols = data.keys()
	fields = []
	for col in cols:
		fields.append(data[col])
	query = 'INSERT INTO `%s` (`%s`) VALUES (%s)' % (table, '`, `'.join(cols), ', '.join(['%s'] * len(fields)))
	return (query, fields)

def build_replace(table, data):
	query = 'REPLACE INTO `%s` SET ' % table
	query += ('`%s` = %%s' * len(data)) % tuple(data.keys())
	return (query, data.values())

class Store(object):
	_saved_guids = []
	_factories = {}
	
	def __init__(self, guid_table='guid', **kwargs):
		self.conn = MySQLdb.connect(kwargs['host'], kwargs['user'], kwargs['pass'], kwargs['db'])
		self.cursor = conn.cursor(cursors.SSDictCursor)
		self.guid_table = guid_table
		
		global _current_store
		if(_current_store):
			raise RuntimeError("Only one Store instance may be created.")
		_current_store = self
	
	def get_guid(self, increment=1):
		if not(self.guid_table):
			return None
		
		result = self.cursor.execute('LOCK TABLES `%s` WRITE', [self.guid_table])
		result = self.cursor.execute('SELECT guid FROM `%s`', [self.guid_table])
		
		guid = self.cursor.fetchone()['guid']
		
		result = self.cursor.execute('UPDATE `%s` SET guid = %s', [self.guid_table, guid + increment])
		result = self.cursor.execute('UNLOCK TABLES')
		
		return guid
	
	def register_factory(table, factory):
		if not(isinstance(factory, Factory)):
			raise ValueError('%r is not a Factory subclass' % factory)
		self._factories[table] = factory
	
	def has_factory(table):
		return table in self._factories
	
	def ensure_factory(table, model_class):
		if(table not in self._factories):
			self.register_factory(table, storable.DefaultFactory(table, model_class)
	
	
