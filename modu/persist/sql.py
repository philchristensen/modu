# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
SQL building facilities.
"""

import types

def build_insert(table, data):
	"""
	Given a table name and a dictionary, construct an INSERT query. Keys are
	sorted alphabetically before output, so the result of passing a semantically
	identical dictionary should be the same every time.
	
	Use modu.sql.RAW to embed SQL directly in the VALUES clause.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	"""
	if not(data):
		raise ValueError("`data` argument to build_insert() is empty.")
	if not(isinstance(data, (list, tuple))):
		data = [data]
	
	table = escape_dot_syntax(table)
	keys = data[0].keys()
	keys.sort()
	
	values = []
	query = 'INSERT INTO %s (`%s`) VALUES ' % (table, '`, `'.join(keys))
	for index in range(len(data)):
		row = data[index]
		values.extend([row[key] for key in keys])
		query += '(' + ', '.join(['%s'] * len(row)) + ')'
		if(index < len(data) - 1):
			query += ', '
	
	return interp(query, values)


def build_replace(table, data):
	"""
	Given a table name and a dictionary, construct an REPLACE INTO query. Keys are
	sorted alphabetically before output, so the result of running a semantically
	identical dictionary should be the same every time.
	
	Use modu.sql.RAW to embed SQL directly in the SET clause.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL query
	@rtype: str
	"""
	table = escape_dot_syntax(table)
	query_stub = 'REPLACE INTO %s ' % table
	return query_stub + build_set(data)

def build_set(data):
	"""
	Given a dictionary, construct a SET clause. Keys are sorted alphabetically
	before output, so the result of passing a semantically identical dictionary
	should be the same every time.
	
	@param data: a column name to value map
	@type data: dict
	
	@returns: an SQL fragment
	@rtype: str
	"""
	keys = data.keys()
	keys.sort()
	values = [data[key] for key in keys]
	set_clause = 'SET %s' % (', '.join(['`%s` = %%s'] * len(data)) % tuple(keys))
	return interp(set_clause, values)


def build_update(table, data, constraints):
	"""
	Given a table name, a dictionary, and a set of constraints, construct an UPDATE
	query. Keys are sorted alphabetically before output, so the result of passing
	a semantically identical dictionary should be the same every time.
	
	@param table: the desired table name
	@type table: str
	
	@param data: a column name to value map
	@type data: dict
	
	@param constraints: a column name to value map
	@type constraints: dict
	
	@returns: an SQL query
	@rtype: str
	
	@seealso: L{build_where()}
	"""
	table = escape_dot_syntax(table)
	query_stub = 'UPDATE %s ' % table
	return query_stub + build_set(data) + ' ' + build_where(constraints)


def build_select(table, data):
	"""
	Given a table name and a dictionary, construct a SELECT query. Keys are
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
	table = escape_dot_syntax(table)
	if('__select_keyword' in data):
		query = "SELECT %s * FROM %s " % (data['__select_keyword'], table)
	else:
		query = "SELECT * FROM %s " % table
	
	return query + build_where(data)


def build_delete(table, constraints):
	"""
	Given a table name, and a set of constraints, construct a DELETE query.
	Keys are sorted alphabetically before output, so the result of passing
	a semantically identical dictionary should be the same every time.
	
	@param table: the desired table name
	@type table: str
	
	@param constraints: a column name to value map
	@type constraints: dict
	
	@returns: an SQL query
	@rtype: str
	
	@seealso: L{build_where()}
	"""
	table = escape_dot_syntax(table)
	query_stub = 'DELETE FROM %s ' % table
	return query_stub + build_where(constraints)


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
		- B{sql.RAW objects}:	result in directly embedded SQL, such that
									C{'col1':RAW("%s = ENCRYPT('whatever')")} equals
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
		key = escape_dot_syntax(key)
		if(isinstance(value, list) or isinstance(value, tuple)):
			criteria.append('%s IN (%s)' % (key, ', '.join(['%s'] * len(value))))
			values.extend(value)
		elif(isinstance(value, RAW)):
			if(value.value.find('%s') != -1):
				criteria.append(value.value % key)
			else:
				criteria.append('%s%s' % (key, value.value))
		elif(value is None):
			criteria.append('ISNULL(%s)' % key)
		elif(isinstance(value, NOT)):
			criteria.append('%s <> %%s' % key)
			values.append(value.value)
		else:
			criteria.append('%s = %%s' % key)
			values.append(value)
	
	if(criteria):
		query += 'WHERE '
		query += ' AND '.join(criteria)
	if('__order_by' in data):
		query += ' ORDER BY %s' % data['__order_by']
	if('__limit' in data):
		query += ' LIMIT %s' % data['__limit']
	
	return interp(query, values)


def escape_dot_syntax(key):
	"""
	Take a table name and check for dot syntax. Escape
	the table name properly with quotes; this currently
	only supports the MySQL syntax, but will hopefully
	be abstracted away soon.
	"""
	dot_index = key.find('.')
	if(dot_index == -1):
		key = '`%s`' % key
	else:
		key = key.replace('.', '.`') + '`'
	return key


def interp(query, args):
	"""
	Interpolate the provided arguments into the provided query, using
	the DB-API's default conversions, with the additional 'RAW' support
	from modu.sql.RAW2Literal
	
	@param query: A query string with placeholders
	@type query: str
	
	@param args: A list of query values
	@type args: sequence
	
	@returns: an interpolated SQL query
	@rtype: str
	"""
	#FIXME: an unfortunate MySQLdb dependency, for now
	import MySQLdb
	from MySQLdb import converters
	
	def UnicodeConverter(s, d):
		return converters.string_literal(s.encode('utf8', 'replace'))
	
	conv_dict = converters.conversions.copy()
	# This is only used in build_replace/insert()
	conv_dict[RAW] = Raw2Literal
	conv_dict[types.UnicodeType] = UnicodeConverter
	return query % MySQLdb.escape_sequence(args, conv_dict)


def Raw2Literal(o, d):
	"""
	Provides conversion support for RAW
	"""
	return o.value


class NOT:
	"""
	Allows NOTs to be embedded in constructed queries.
	
	When persist.NOT(value) is included in the constraint array passed
	to a query building function, it will generate the SQL fragment
	'column <> value'
	
	@ivar value: The value to NOT be
	"""
	def __init__(self, value):
		"""
		Create a NOT instance
		"""
		self.value = value
	
	def __repr__(self):
		"""
		Printable version.
		"""
		return "NOT(%r)" % self.value


class RAW:
	"""
	Allows RAW SQL to be embedded in constructed queries.
	
	@ivar value: "Raw" (i.e., properly escaped) SQL
	"""
	def __init__(self, value):
		"""
		Create a RAW SQL fragment
		"""
		self.value = value
	
	def __repr__(self):
		"""
		Printable version.
		"""
		return "RAW(%s)" % self.value


