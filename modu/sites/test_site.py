# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
ISite implementors and sample resource classes used in the testing framework.

Since the ISite implementors don't actually use real (or even valid)
hostnames, none of these sites should ever activate in normal use.
"""

from twisted import plugin

from zope.interface import classProvides, implements

from modu.web import app, resource

class TestResource(resource.Resource):
	"""
	This simple resource returns plaintext containing
	the postpath used in the request.
	"""
	implements(resource.IContent)
	
	def get_paths(self):
		"""
		@see: L{modu.web.app.resource.IResource.get_paths()}
		"""
		return ['/test-resource']
	
	def prepare_content(self, req):
		"""
		@see: L{modu.web.app.resource.IContent.prepare_content()}
		"""
		pass
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.app.resource.IContent.get_content_type()}
		"""
		return 'text/plain'
	
	def get_content(self, req):
		"""
		@see: L{modu.web.app.resource.IContent.get_content()}
		"""
		return '/'.join(req.postpath)


class TestDelegateResource(resource.Resource):
	"""
	This resource delegate will return an instance of
	TestResource.
	"""
	implements(resource.IResourceDelegate)
	
	def get_paths(self):
		"""
		@see: L{modu.web.app.resource.IResource.get_paths()}
		"""
		return ['/test-delegate']
	
	def get_delegate(self, req):
		"""
		@see: L{modu.web.app.resource.IResourceDelegate.get_delegate()}
		"""
		return TestResource()



class TestAccessControlResource(resource.Resource):
	"""
	This resource will always return a 401 Unauthorized when
	requested.
	"""
	implements(resource.IAccessControl)
	
	def get_paths(self):
		"""
		@see: L{modu.web.app.resource.IResource.get_paths()}
		"""
		return ['/test-access']
	
	def check_access(self, req):
		"""
		@see: L{modu.web.app.resource.IAccessControl.check_access()}
		"""
		app.raise401(req.path)


class BasicTestSite(object):
	"""
	This site activates only the most basic features of modu, running at /app-test.
	"""
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		"""
		@see: L{modu.app.ISite.initialize()}
		"""
		application.base_domain = '____basic-test-domain____:1234567'
		application.base_path = '/app-test'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(TestResource)
		application.activate(TestDelegateResource)
		application.activate(TestAccessControlResource)


class BasicRootTestSite(object):
	"""
	This site activates only the most basic features of modu, running at the site root.
	"""
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		"""
		@see: L{modu.app.ISite.initialize()}
		"""
		application.base_domain = '____basic-test-domain____:1234567'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False
		application.activate(TestResource)
		application.activate(TestDelegateResource)
		application.activate(TestAccessControlResource)


class StoreTestSite(object):
	"""
	This site activates a database connection and a Store.
	"""
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		"""
		@see: L{modu.app.ISite.initialize()}
		"""
		application.base_domain = '____store-test-domain____:1234567'
		application.base_path = '/app-test'
		application.session_class = None
		application.activate(TestResource)
		application.activate(TestDelegateResource)
		application.activate(TestAccessControlResource)


