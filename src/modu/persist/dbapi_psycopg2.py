# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Configures psycopg2 driver-specific aspects of the db layer.
"""

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
