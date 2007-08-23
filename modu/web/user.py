# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.persist import storable

def get_grant_tree(store):
	store.ensure_factory('__grant')
	grant_query = """SELECT CONCAT(r.id, '-', p.id) AS id, r.name AS role, p.name AS permission
					FROM role r
						INNER JOIN permission p ON (p.role_id = r.id)
					ORDER BY r.name"""
	
	grants = store.load('__grant', grant_query)
	tree = {}
	if(grants):
		for grant in grants:
			tree.setdefault(grant.role, []).append(grant.permission)
	return tree


class User(storable.Storable):
	def __init__(self):
		super(User, self).__init__('user')
		self._roles = {}
		self._permissions = {}
	
	def is_allowed(self, permission):
		self.__load_roles()
		if(isinstance(permission, (list, tuple))):
			result = filter(None, [self.is_allowed(perm) for perm in permission])
			if(len(result) == len(permission)):
				return True
			else:
				return False
		else:
			grant_tree = get_grant_tree(self.get_store())
			for role in self._roles:
				if(permission in grant_tree.get(role, [])):
					return True
			return False
	
	def has_role(self, role):
		self.__load_roles()
		return role in self._roles
	
	def __load_roles(self):
		if(self._roles):
			return
		
		store = self.get_store()
		
		store.ensure_factory('role', Role)
		role_query = """SELECT r.*
						FROM role r
							INNER JOIN user_role ur ON (ur.role_id = r.id)
						WHERE ur.user_id = %d""" % self.get_id()
		roles = store.load('role', role_query)
		if(roles):
			for role in roles:
				self._roles[role.name] = role

class AnonymousUser(User):
	def is_allowed(self, permission):
		return False
	
	def has_role(self, role):
		return False
	
	def get_data(self):
		raise RuntimeError('It is not possible to save the anonymous user object.')
	
	def get_id(self):
		return 0
	
	def set_id(self):
		raise RuntimeError('It is not possible to set the ID of the anonymous user object.')

class Role(storable.Storable):
	def __init__(self):
		super(Role, self).__init__('role')

class Permission(storable.Storable):
	def __init__(self):
		super(Permission, self).__init__('permission')
