# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
An example site configuration for the AdminResource tool.
"""

import os.path

from zope.interface import classProvides

from twisted import plugin

from modu.web import resource, app, static
from modu.editable.resource import AdminResource

class AdminSite(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		application.base_path = '/modu/examples/admin'
		application.base_domain = 'localhost'
		application.activate(AdminResource('/'))
		
		import modu
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(static.FileResource(['/assets'], modu_assets_path))
