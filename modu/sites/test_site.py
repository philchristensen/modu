# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted import plugin

from zope.interface import classProvides, implements

from modu.web import app, resource

class TestResource(resource.Resource):
	implements(resource.IContent)
	
	def get_paths(self):
		return ['/test-resource']
	
	def prepare_content(self, req):
		pass
	
	def get_content_type(self, req):
		return 'text/plain'
	
	def get_content(self, req):
		return '/'.join(req.app.tree.postpath)


class TestDelegateResource(resource.Resource):
	implements(resource.IResourceDelegate)
	
	def get_paths(self):
		return ['/test-delegate']
	
	def get_delegate(self, req):
		return TestResource()



class TestAccessControlResource(resource.Resource):
	implements(resource.IResourceDelegate)
	
	def get_paths(self):
		return ['/test-access']
	
	def check_access(self, req):
		app.raise401(req.path)


class BasicTestSite(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		application.base_domain = '____basic-test-domain____:1234567'
		application.base_path = '/app-test'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(TestResource())
		application.activate(TestDelegateResource())
		application.activate(TestAccessControlResource())


