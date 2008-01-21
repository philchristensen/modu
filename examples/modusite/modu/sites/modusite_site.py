# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

import os, os.path

from zope.interface import classProvides

from twisted import plugin

import modu
from modu.web import app, static
from modu.web.resource import WSGIPassthroughResource
from modu.editable import resource
from modu.editable.datatypes import fck

import modusite
from modusite.resource import index, modutrac, blog

class Site(object):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'localhost'
	
	def configure_request(self, req):
		compiled_template_root = os.path.join(req.approot, 'var')
		if(os.path.exists(compiled_template_root)):
			req.app.config['compiled_template_root'] = compiled_template_root
		
		req['trac.env_path'] = os.path.abspath(os.path.join(os.path.dirname(modusite.__file__), '../trac'))
	
	def initialize(self, application):
		application.base_domain = self.hostname
		application.db_url = 'MySQLdb://modusite:yibHikmet3@localhost/modusite'
		
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(static.FileResource, ['/assets'], modu_assets_path)
		
		application.activate(resource.AdminResource, default_listing='page')
		application.activate(fck.FCKEditorResource)
		application.activate(index.Resource)
		application.activate(blog.Resource)
		
		os.environ['PYTHON_EGG_CACHE'] = '/tmp'
		
		import trac
		trac_htdocs_path = os.path.join(os.path.dirname(trac.__file__), 'htdocs')
		application.activate(static.FileResource, ['/trac/chrome/common'], trac_htdocs_path)
		application.activate(modutrac.Resource)

class megatron_local(Site):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'megatron.local'

class modu_bubblehouse_org(Site):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'modu.bubblehouse.org'
	
	def initialize(self, application):
		super(modu_bubblehouse_org, self).initialize(application)
		os.environ['PYTHON_EGG_CACHE'] = '/var/cache/eggs'
