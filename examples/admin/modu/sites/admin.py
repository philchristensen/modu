# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os.path

from zope.interface import classProvides

from twisted import plugin

from modu.web import resource, app
from modu.editable.resource import AdminResource

class AdminSite(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		application.base_path = '/modu/examples/admin'
		application.base_domain = 'localhost'
		application.activate(AdminResource('/'))
		
		import modu
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(resource.FileResource(['/assets'], modu_assets_path))
