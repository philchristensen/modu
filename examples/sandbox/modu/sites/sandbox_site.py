# Modu Sandbox
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

import os.path

import pkg_resources as pkg

from zope.interface import classProvides

from twisted import plugin

from modu.web import app, static
from modu.editable import resource
from modu.editable.datatypes import fck

from sandbox.resource import index, zpt, cherry, form

class Site(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		application.base_domain = 'localhost'
		
		application.compiled_template_root = '/tmp/modu/sandbox'
		if not(os.path.exists(application.compiled_template_root)):
			os.makedirs(application.compiled_template_root)

		application.db_url = 'MySQLdb://sandbox:sandbox@localhost/sandbox'
		application.activate('/assets', static.FileResource, pkg.resource_filename('modu.assets', ''))
		
		application.activate('/admin', resource.AdminResource, default_listing='page')
		application.activate('/fck', fck.FCKEditorResource)
		
		application.activate('/', index.Resource)
		application.activate('/zpt', zpt.Resource)
		application.activate('/cherry', cherry.Resource)
		application.activate('/form', form.Resource)
