# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import crypt

from modu.persist import storable, sql
from modu.util import form

# this needs to be cached somehow, but we don't want it to
# bleed over into other stores or applications
def get_grant_tree(store):
	store.ensure_factory('__grant')
	grant_query = """SELECT CONCAT(r.id, '-', p.id) AS id, r.name AS role, p.name AS permission
					FROM role r
						INNER JOIN (role_permission rp
							INNER JOIN permission p ON (rp.permission_id = p.id))
						ON (rp.role_id = r.id)
					ORDER BY r.name"""
	
	grants = store.load('__grant', grant_query)
	tree = {}
	if(grants):
		for grant in grants:
			tree.setdefault(grant.role, []).append(grant.permission)
	return tree

def get_role_assignments(store):
	"""
	Return a list of users for each available role.
	"""
	assignment_query = """SELECT r.id, r.name,
								GROUP_CONCAT(concat(u.id, '|', u.username, '|', u.first, '|', u.last)) AS members
							FROM role r
								INNER JOIN (user_role ur
									INNER JOIN user u ON ur.user_id = u.id)
								ON ur.role_id = r.id
							WHERE NOT(INSTR(u.username, 'stats'))
							GROUP BY r.id"""
	
	store.pool.runOperation('SET @OLD_GROUP_CONCAT_MAX_LEN=@@GROUP_CONCAT_MAX_LEN;')
	store.pool.runOperation('SET GROUP_CONCAT_MAX_LEN = 32768;')
	results = store.pool.runQuery(assignment_query)
	store.pool.runOperation('SET GROUP_CONCAT_MAX_LEN = @OLD_GROUP_CONCAT_MAX_LEN;')
	
	assignments = []
	for row in results:
		assignments.append(dict(
			id		= row['id'],
			name	= row['name'],
			members	= [
				dict(zip(('id', 'username', 'first', 'last'), member.split('|')))
					for member in row['members'].split(',')
			]
		))
	
	return assignments

def authenticate_user(req, username, password):
	user_class = getattr(req.app, 'user_class', User)
	req.store.ensure_factory('user', user_class)
	
	u = req.store.load_one('user', username=username)
	if(u.crypt == crypt.crypt(password, u.crypt[:2])):
		return u
	
	return None

def validate_login(req, form):
	"""
	Validation callback for login form.
	
	Ensures values in username and password fields.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param form: the form being validated
	@type form: L{modu.util.form.FormNode}
	
	@return: True if all data is entered
	@rtype: bool
	"""
	if not(req.data[form.name]['username']):
		form.set_form_error('username', "Please enter your username.")
	if not(req.data[form.name]['password']):
		form.set_form_error('password', "Please enter your password.")
	return not form.has_errors()


def submit_login(req, form):
	"""
	Submission callback for login form.
	
	Logs in the user using crypt()-based passwords.
	
	@param req: the current request
	@type req: L{modu.web.app.Request}
	
	@param form: the form being validated
	@type form: L{modu.util.form.FormNode}
	"""
	form_data = req.data[form.name]
	u = authenticate_user(req, form_data['username'].value, form_data['password'].value)
	if(u):
		req.session.set_user(u)
		return True
	else:
		req.messages.report('error', "Sorry, that login was incorrect.")
	return False


def get_default_login_form():
	login_form = form.FormNode('login')
	
	login_form['username'](type='textfield', label='Username')
	login_form['password'](type='password', label='Password')
	login_form['submit'](type='submit', value='login')
	login_form.validate = validate_login
	login_form.submit = submit_login
	
	return login_form


class User(storable.Storable):
	def __init__(self):
		super(User, self).__init__('user')
		self._roles = None
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
			for role in self._roles:
				if(permission in self._grant_tree.get(role, [])):
					return True
			return False
	
	def has_role(self, role):
		self.__load_roles()
		return role in self._roles
	
	def get_roles(self):
		self.__load_roles()
		return self._roles
	
	def __load_roles(self):
		if(self._roles is not None):
			return
		
		store = self.get_store()
		
		store.ensure_factory('role', Role)
		role_query = """SELECT r.*
						FROM role r
							INNER JOIN user_role ur ON (ur.role_id = r.id)
						WHERE ur.user_id = %d""" % self.get_id()
		roles = store.load('role', role_query)
		self._roles = {}
		if(roles):
			for role in roles:
				self._roles[role.name] = role
		
		self._grant_tree = get_grant_tree(self.get_store())

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
