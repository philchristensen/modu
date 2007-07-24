# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import MySQLdb

from distutils.version import LooseVersion

def connect(dsn):
	conn = MySQLdb.connect(dsn['host'], dsn['user'], dsn['password'], dsn['path'][1:])
	fix_mysqldb(conn)
	return conn


def fix_mysqldb(connection):
	"""
	fix character_set_name() bug in MySQLdb < 1.2.2
	"""
	if(LooseVersion(MySQLdb.__version__) < LooseVersion('1.2.2')):
		def _yes_utf8_really(self):
			return 'utf-8'
		
		instancemethod = type(_DummyClass._dummy_method)
		
		connection.character_set_name = instancemethod(_yes_utf8_really, connection, connection.__class__)


class _DummyClass(object):
	def _dummy_method(self):
		pass

