# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.persist import storable

class User(storable.Storable):
	def __init__(self):
		super(User, self).__init__('user')

class AnonymousUser(User):
	def get_data(self):
		raise RuntimeError('It is not possible to save the anonymous user object.')
	
	def get_id(self, fetch=False):
		return 0
	
	def set_id(self):
		raise RuntimeError('It is not possible to set the ID of the anonymous user object.')

