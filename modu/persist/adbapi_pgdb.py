# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def process_dsn(dsn):
	dsn['password'] = dsn['passwd']
	del dsn['passwd']
	dsn['database'] = dsn['db']
	del dsn['db']
	return [], dsn
