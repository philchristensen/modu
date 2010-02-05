# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu.persist import storable, sql
from modusite.model import release

class Project(storable.Storable):
	def __init__(self):
		super(Project, self).__init__('project')
	
	def get_releases(self):
		store = self.get_store()
		store.ensure_factory('release', release.Release)
		return store.load('release', dict(
			project_id	= self.get_id(),
			nightly		= sql.RAW('IFNULL(%s, 0) = 0'),
			active		= 1,
			__order_by	= "version_weight DESC",
		))
	
	def get_nightly(self):
		store = self.get_store()
		store.ensure_factory('release', release.Release)
		return store.load_one('release', dict(
			project_id	= self.get_id(),
			nightly		= 1,
			active		= 1,
			__order_by	= "version_weight DESC",
		))
