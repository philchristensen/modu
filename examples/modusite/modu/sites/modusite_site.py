# modusite
# Copyright (C) 2008 modusite
#
# $Id$
#

import os.path

from zope.interface import classProvides

from twisted import plugin

import modu
from modu.web import app, static
from modu.web.resource import WSGIPassthroughResource
from modu.editable import resource
from modu.editable.datatypes import fck

import modusite
from modusite.resource import index, modutrac

class Site(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def configure_request(self, req):
		compiled_template_root = os.path.join(req.approot, 'var')
		if(os.path.exists(compiled_template_root)):
			req.app.config['compiled_template_root'] = compiled_template_root
		
		req['trac.env_path'] = os.path.abspath(os.path.join(os.path.dirname(modusite.__file__), '../trac'))
	
	def initialize(self, application):
		application.base_domain = 'localhost'
		application.db_url = 'MySQLdb://modusite:yibHikmet3@localhost/modusite'
		
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(static.FileResource, ['/assets'], modu_assets_path)
		
		application.activate(resource.AdminResource, default_listing='page')
		application.activate(fck.FCKEditorResource)
		application.activate(index.Resource)
		
		import trac
		trac_htdocs_path = os.path.join(os.path.dirname(trac.__file__), 'htdocs')
		application.activate(static.FileResource, ['/trac/chrome/common'], trac_htdocs_path)
		application.activate(modutrac.Resource)
