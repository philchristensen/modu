import MySQLdb, warnings
from MySQLdb import cursors, converters

from dathomir.persist import storable

_current_store = None

def get_store():
	global _current_store
	return _current_store

def build_insert(table, data):
	query = 'INSERT INTO `%s` (`%s`) VALUES (%s)' % (table, '`, `'.join(data.keys()), ', '.join(['%s'] * len(data)))
	return query, data.values()

def build_replace(table, data):
	query = 'REPLACE INTO `%s` SET ' % table
	query += ', '.join(['`%s` = %%s'] * len(data)) % tuple(data.keys())
	return query, data.values()

def build_select(table, data):
	if('__select_keyword' in data):
		query = "SELECT %s * FROM `%s` " % (data['__select_keyword'], table)
	else:
		query = "SELECT * FROM `%s` " % table
	
	criteria = []
	values = []
	for key in data:
		if(key.startswith('_')):
			continue
		value = data[key]
		if(isinstance(value, list) or isinstance(value, tuple)):
			criteria.append('`%s` IN (%s)' % (key, ', '.join(['%s'] * len(value))))
			values.extend(value)
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
	
	return query, values

class raw(object):
	def __init__(self, sql):
		self.sql = sql
	
	def __str__(self, sql):
		return str(sql)

class Store(object):
	_saved_guids = []
	_factories = {}
	_guid_table = None
	
	def __init__(self, host='localhost', guid_table='guid', **kwargs):
		conv_dict = converters.conversions.copy()
		#conv_dict[raw] = str
		self.connection = MySQLdb.connect(host, kwargs['user'], kwargs['password'], kwargs['db'], conv=conv_dict)
		
		self._guid_table = guid_table
		
		global _current_store
		if(_current_store):
			raise RuntimeError("Only one Store instance may be created.")
		_current_store = self
	
	def get_guid(self, increment=1):
		if not(self.uses_guids()):
			return None
		
		cur = self.connection.cursor(cursors.SSDictCursor)
		
		result = cur.execute('LOCK TABLES `%s` WRITE' % self._guid_table)
		result = cur.execute('SELECT `guid` FROM `%s`' % self._guid_table)
		
		guid = cur.fetchall()[0]['guid']
		
		result = cur.execute('UPDATE `%s` SET `guid` = %%s' % self._guid_table, [guid + increment])
		result = cur.execute('UNLOCK TABLES')
		
		return guid
	
	def uses_guids(self):
		return self._guid_table != None
	
	def register_factory(self, table, factory):
		if not(isinstance(factory, Factory)):
			raise ValueError('%r is not a Factory subclass' % factory)
		self._factories[table] = factory
	
	def has_factory(self, table):
		return table in self._factories
	
	def ensure_factory(self, table, model_class=storable.Storable):
		if(table not in self._factories):
			self.register_factory(table, storable.DefaultFactory(table, model_class))
	
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
		cur = self.connection.cursor(cursors.SSDictCursor)
		
		if(id):
			data[storable.ID_COLUMN] = id
			query = build_replace(table, data)
		else:
			query = build_insert(table, data)
			cur.execute('LOCK TABLES `%s` WRITE' % table)
		print query
		cur.execute(*query)
		
		if not(id):
			cur.execute('SELECT MAX(%s) AS id FROM `%s`' % (storable.ID_COLUMN, table))
			storable.set_id(self.cursor.fetchone()['id'])
			cur.execute('UNLOCK TABLES' % table)

