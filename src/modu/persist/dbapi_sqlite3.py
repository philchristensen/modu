# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Configures sqlite3 driver-specific aspects of the db layer.
"""

import sqlite3

from modu.persist import sql

sqlite3.register_adapter(sql.RAW, lambda o: o.value)

def use_bytestrings(connection):
	import sqlite3
	
	connection.text_factory = str

def process_dsn(dsn):
	"""
	Take a standard DSN-dict and return the args and
	kwargs that will be passed to the sqlite3 Connection
	constructor.
	"""
	return [dsn['db']], {'cp_openfun' : use_bytestrings}