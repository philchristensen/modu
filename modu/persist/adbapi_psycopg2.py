# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def process_dsn(dsn):
	"""
	Take a standard DSN-dict and return the args and
	kwargs that will be passed to the psycopg2 Connection
	constructor.
	"""
	args = ['host=%s dbname=%s user=%s password=%s' % (dsn['host'], dsn['db'], dsn['user'], dsn['passwd'])]
	del dsn['host']
	del dsn['db']
	del dsn['user']
	del dsn['passwd']
	return args, dsn
