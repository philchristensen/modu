# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Configures MySQLdb driver-specific aspects of the db layer.
"""

def process_dsn(dsn):
	"""
	Take a standard DSN-dict and return the args and
	kwargs that will be passed to the MySQLdb Connection
	constructor.
	
	We use the t.e.adbapi.ConnectionPool kwargs here to
	provide a callback that fixes broken connections,
	and set the default cursorclass.
	"""
	dsn['cp_openfun'] = fix_mysqldb
	from MySQLdb import cursors
	dsn['cursorclass'] = cursors.SSDictCursor
	
	# I'm just not sure whether these make things worse or better
	# dsn['use_unicode'] = True
	# dsn['charset'] = 'utf8'
	return [], dsn


def fix_mysqldb(connection):
	"""
	This function takes a MySQLdb connection object and replaces
	character_set_name() if the version of MySQLdb < 1.2.2.
	
	It also enables NO_BACKSLASH_ESCAPES per session.
	"""
	cur = connection.cursor()
	cur.execute("SET SESSION sql_mode='NO_BACKSLASH_ESCAPES'")
	cur.close()
	
	from distutils.version import LooseVersion
	import MySQLdb
	if(LooseVersion(MySQLdb.__version__) < LooseVersion('1.2.2')):
		def _yes_utf8_really(self):
			return 'utf8'
		
		instancemethod = type(_DummyClass._dummy_method)
		
		connection.character_set_name = instancemethod(_yes_utf8_really, connection, connection.__class__)


class _DummyClass(object):
	"""
	Dummy class used to override an instance method on MySQLdb connection object.
	"""
	def _dummy_method(self):
		"""
		Sample instance method for hackery.
		"""
		pass