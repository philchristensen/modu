# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def process_dsn(dsn):
	args = ['host=%s dbname=%s user=%s password=%s' % (dsn['host'], dsn['db'], dsn['user'], dsn['passwd'])]
	del dsn['host']
	del dsn['db']
	del dsn['user']
	del dsn['passwd']
	return args, dsn
