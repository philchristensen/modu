# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
Configures Sphinx-via-MySQLdb driver-specific aspects of the db layer.
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
	from MySQLdb import cursors
	dsn['cursorclass'] = cursors.SSDictCursor
	dsn['override_driver'] = 'MySQLdb'
	
	# I'm just not sure whether these make things worse or better
	# dsn['use_unicode'] = True
	# dsn['charset'] = 'utf8'
	return [], dsn
