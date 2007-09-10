# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu.persist import storable, adbapi
from modu.util import test
from modu.web import user, app
from modu import persist

TEST_TABLES = """
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` bigint(20),
  `username` varchar(255),
  `first` varchar(255),
  `last` varchar(255),
  `crypt` varchar(255),
  PRIMARY KEY (id),
  UNIQUE KEY `username_idx` (`username`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;

DROP TABLE IF EXISTS `user_role`;
CREATE TABLE IF NOT EXISTS `user_role` (
  `user_id` bigint(20),
  `role_id` bigint(20),
  PRIMARY KEY (`user_id`, `role_id`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;

DROP TABLE IF EXISTS `role`;
CREATE TABLE IF NOT EXISTS `role` (
  `id` bigint(20),
  `name` varchar(255),
  PRIMARY KEY (id),
  UNIQUE KEY `name_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;

DROP TABLE IF EXISTS `role_permission`;
CREATE TABLE IF NOT EXISTS `role_permission` (
  `role_id` bigint(20),
  `permission_id` bigint(20),
  PRIMARY KEY (`role_id`, `permission_id`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;

DROP TABLE IF EXISTS `permission`;
CREATE TABLE IF NOT EXISTS `permission` (
  `id` bigint(20),
  `name` varchar(255),
  PRIMARY KEY (id),
  UNIQUE KEY `perm_idx` (`name`)
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;

DROP TABLE IF EXISTS `guid`;
CREATE TABLE `guid` (
  `guid` bigint(20) unsigned
) ENGINE=MyISAM DEFAULT CHARACTER SET utf8;
"""

class UserTestCase(unittest.TestCase):
	def setUp(self):
		store = persist.Store.get_store()
		if not(store):
			store = persist.Store(adbapi.connect('MySQLdb://modu:modu@localhost/modu'))
		
		global TEST_TABLES
		for sql in TEST_TABLES.split(";"):
			if(sql.strip()):
				try:
					store.pool.runOperation(sql)
				except store.pool.dbapi.Warning:
					pass
		
		self.store = store
		
		self.store.ensure_factory('user', user.User)
		self.store.ensure_factory('role', user.Role)
		self.store.ensure_factory('permission', user.Permission)
	
	def test_basic(self):
		u = user.User()
		u.username = 'phil@bubblehouse.org'
		u.first = 'Phil'
		u.last = 'Christensen'
		u.crypt = persist.RAW("ENCRYPT('phil')")
		self.store.save(u)
		
		r = user.Role()
		r.name = 'Authenticated User'
		self.store.save(r)
		
		p = user.Permission()
		p.name = 'view item'
		self.store.save(p)
		
		self.store.pool.runOperation("INSERT INTO user_role (user_id, role_id) VALUES (%s, %s)", [u.get_id(), r.get_id()])
		self.store.pool.runOperation("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)", [r.get_id(), p.get_id()])
		
		self.failUnless(u.is_allowed('view item'), 'User cannot "view item"')
	
	def test_multiple_perms(self):
		u = user.User()
		u.username = 'phil@bubblehouse.org'
		u.first = 'Phil'
		u.last = 'Christensen'
		u.crypt = persist.RAW("ENCRYPT('phil')")
		self.store.save(u)
		
		r = user.Role()
		r.name = 'Authenticated User'
		self.store.save(r)
		
		self.store.pool.runOperation("INSERT INTO user_role (user_id, role_id) VALUES (%s, %s)", [u.get_id(), r.get_id()])

		p = user.Permission()
		p.name = 'view item'
		self.store.save(p)
		
		self.store.pool.runOperation("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)", [r.get_id(), p.get_id()])
		
		p = user.Permission()
		p.name = 'edit item'
		self.store.save(p)
		
		self.store.pool.runOperation("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)", [r.get_id(), p.get_id()])
		
		self.failUnless(u.is_allowed('view item'), 'User cannot "view item"')
		self.failUnless(u.is_allowed('edit item'), 'User cannot "edit item"')
		self.failUnless(u.is_allowed(['view item', 'edit item']), 'User cannot "view item" and "edit item"')
		
	
	def test_multiple_roles(self):
		u = user.User()
		u.username = 'phil@bubblehouse.org'
		u.first = 'Phil'
		u.last = 'Christensen'
		u.crypt = persist.RAW("ENCRYPT('phil')")
		self.store.save(u)
		
		auth_role = user.Role()
		auth_role.name = 'Authenticated User'
		self.store.save(auth_role)
		
		admin_role = user.Role()
		admin_role.name = 'Admin User'
		self.store.save(admin_role)
		
		self.store.pool.runOperation("INSERT INTO user_role (user_id, role_id) VALUES (%s, %s)", [u.get_id(), auth_role.get_id()])
		self.store.pool.runOperation("INSERT INTO user_role (user_id, role_id) VALUES (%s, %s)", [u.get_id(), admin_role.get_id()])
		
		p = user.Permission()
		p.name = 'view item'
		self.store.save(p)
		
		self.store.pool.runOperation("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)", [auth_role.get_id(), p.get_id()])
		
		p = user.Permission()
		p.name = 'edit item'
		self.store.save(p)
		
		self.store.pool.runOperation("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)", [admin_role.get_id(), p.get_id()])
		
		self.failUnless(u.is_allowed('view item'), 'User cannot "view item"')
		self.failUnless(u.is_allowed('edit item'), 'User cannot "edit item"')
		self.failUnless(u.is_allowed(['view item', 'edit item']), 'User cannot "view item" and "edit item"')
		
		
		