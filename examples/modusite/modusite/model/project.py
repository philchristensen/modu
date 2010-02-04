# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu.persist import storable

from modusite.model import release

class Project(storable.Storable):
	def __init__(self):
		super(Project, self).__init__('project')
	
	def load_data(self, data):
		# Automatically convert binary data to string.
		if(hasattr(data['body'], 'tostring')):
			data['body'] = data['body'].tostring()
		super(Project, self).load_data(data)
	
	def get_releases(self):
		store = self.get_store()
		store.ensure_factory('release', release.Release)
		return store.load('release', project_id=self.get_id())
