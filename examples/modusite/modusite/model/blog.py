# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu.persist import storable

class Blog(storable.Storable):
	@classmethod
	def get_blogs(cls, store, recent=5):
		store.ensure_factory('blog', cls, force=True)
		return store.load('blog', active=1, __order_by='published_date DESC')
	
	def __init__(self):
		super(Blog, self).__init__('blog')
	
	def load_data(self, data):
		# Automatically convert binary data to string.
		if(hasattr(data['body'], 'tostring')):
			data['body'] = data['body'].tostring()
		super(Blog, self).load_data(data)
	
	def get_author_name(self):
		store = self.get_store()
		user = store.load_one(storable.Storable('user'), id=self.published_by)
		return user.username
