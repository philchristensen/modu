# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

from modu.persist import storable

class Release(storable.Storable):
	def __init__(self):
		super(Release, self).__init__('release')
	
