# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu.persist import storable

class Release(storable.Storable):
	def __init__(self):
		super(Release, self).__init__('release')
