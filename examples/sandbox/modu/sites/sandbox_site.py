# Modu Sandbox
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os.path

from zope.interface import classProvides

from twisted import plugin

from modu import assets
from modu.web import app, static
from modu.editable import resource
from modu.editable.datatypes import fck

from sandbox.resource import index, zpt, cherry, form

class Site(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def configure_request(self, req):
		compiled_template_root = os.path.join(req.approot, 'var')
		if(os.path.exists(compiled_template_root)):
			req.app.config['compiled_template_root'] = compiled_template_root
	
	def initialize(self, application):
		application.base_domain = 'localhost'
		
		application.db_url = 'MySQLdb://sandbox:sandbox@localhost/sandbox'
		
		application.activate('/assets', static.FileResource, os.path.dirname(assets.__file__))
		
		application.activate('/admin', resource.AdminResource, default_listing='page')
		application.activate('/fck', fck.FCKEditorResource)
		
		application.activate('/', index.Resource)
		application.activate('/zpt', zpt.Resource)
		application.activate('/cherry', cherry.Resource)
		application.activate('/form', form.Resource)
