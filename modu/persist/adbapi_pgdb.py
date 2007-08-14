# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def process_dsn(dsn):
	"""
	Take a standard DSN-dict and return the args and
	kwargs that will be passed to the pgdb Connection
	constructor.
	"""
	dsn['password'] = dsn['passwd']
	del dsn['passwd']
	dsn['database'] = dsn['db']
	del dsn['db']
	return [], dsn
