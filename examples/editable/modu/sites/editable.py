# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import classProvides

from twisted import plugin

from modu.web.app import ISite
from modu.web import resource
from modu.persist import storable
from modu.editable.datatypes import string, relational

class EditableSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, application):
		application.base_path = '/editable'
		application.base_domain = 'localhost'
		application.activate(editable.EditorResource())
		
		import os.path, modu
		
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(resource.FileResource(['/assets'], modu_assets_path))
