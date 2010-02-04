# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

import os, os.path
import pkg_resources as pkg

from zope.interface import classProvides

from twisted import plugin

import modu
from modu import assets
from modu.web import app, static
from modu.web.resource import WSGIPassthroughResource
from modu.editable import resource
from modu.editable.datatypes import fck

import modusite
from modusite.resource import index, modutrac, blog, faq, downloads

class Site(object):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'localhost'
	
	def configure_request(self, req):
		req['trac.env_path'] = pkg.resource_filename('modusite', 'trac')
	
	def initialize(self, application):
		application.base_domain = self.hostname
		application.db_url = 'MySQLdb://modusite:yibHikmet3@localhost/modusite'
		application.session_cookie_params = {'Path':'/'}
		application.template_dir = 'modusite', 'template'
		
		application.activate('/assets', static.FileResource, pkg.resource_filename('modu.assets', ''))
		
		import modusite.editable.itemdefs as itemdefs
		application.activate('/admin', resource.AdminResource, itemdef_module=itemdefs, default_path='admin/listing/page')
		application.activate('/fck', fck.FCKEditorResource)
		application.activate('/', index.Resource)
		application.activate('/downloads', downloads.Resource)
		application.activate('/blog', blog.Resource)
		application.activate('/faq', faq.Resource)
		
		os.environ['PYTHON_EGG_CACHE'] = '/var/cache/eggs'
		
		application.compiled_template_root = '/tmp/modu/modusite'
		if not(os.path.exists(application.compiled_template_root)):
			os.makedirs(application.compiled_template_root)
		
		trac_htdocs_path = pkg.resource_filename('trac', 'htdocs')
		application.activate('/trac/chrome/common', static.FileResource, trac_htdocs_path)
		
		site_htdocs_path = pkg.resource_filename('modusite', 'trac/htdocs')
		application.activate('/trac/chrome/site', static.FileResource, site_htdocs_path)
		
		application.activate('/trac', modutrac.Resource)
		application.activate(['/trac/login', '/trac/logout'], modutrac.LoginSupportResource)

class megatron_local(Site):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'megatron.local'

class optimus_local(Site):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'optimus.local'

class modu_bubblehouse_org(Site):
	classProvides(plugin.IPlugin, app.ISite)
	hostname = 'modu.bubblehouse.org'
