# modusite
# Copyright (C) 2008 Phil Christensen
#
# $Id$
#

import os, os.path

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
		compiled_template_root = os.path.join(req.approot, 'var')
		if(os.path.exists(compiled_template_root)):
			req.app.config['compiled_template_root'] = compiled_template_root
		
		req['trac.env_path'] = os.path.abspath(os.path.join(os.path.dirname(modusite.__file__), '../trac'))
	
	def initialize(self, application):
		application.base_domain = self.hostname
		application.db_url = 'MySQLdb://modusite:yibHikmet3@localhost/modusite'
		application.session_cookie_params = {'Path':'/'}
		
		application.activate('/assets', static.FileResource, os.path.dirname(assets.__file__))
		
		import modusite.editable.itemdefs as itemdefs
		application.activate('/admin', resource.AdminResource, itemdef_module=itemdefs, default_path='admin/listing/page')
		application.activate('/fck', fck.FCKEditorResource)
		application.activate('/', index.Resource)
		application.activate('/downloads', downloads.DownloadsResource)
		application.activate('/blog', blog.Resource)
		application.activate('/faq', faq.Resource)
		
		os.environ['PYTHON_EGG_CACHE'] = '/var/cache/eggs'
		
		apidocs_path = os.path.abspath(os.path.join(os.path.dirname(modu.__file__), '../apidocs'))
		application.activate('/apidocs', static.FileResource, apidocs_path)
		
		import trac
		trac_htdocs_path = os.path.join(os.path.dirname(trac.__file__), 'htdocs')
		application.activate('/trac/chrome/common', static.FileResource, trac_htdocs_path)
		
		site_htdocs_path = os.path.abspath(os.path.join(os.path.dirname(modusite.__file__), '../trac/htdocs'))
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
