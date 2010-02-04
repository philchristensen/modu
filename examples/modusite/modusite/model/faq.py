# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu.persist import storable

class FAQ(storable.Storable):
	def __init__(self):
		super(FAQ, self).__init__('faq')
	
	def get_answerer(self):
		store = self.get_store()
		store.ensure_factory('user')
		user = store.load_one('user', id=self.answered_by)
		return user.username
