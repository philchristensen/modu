# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
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
	
	def prepare_content(self, req):
		"""
		@see: L{modu.web.app.resource.IContent.prepare_content()}
		"""
		if(req.postpath):
			if(req.postpath[0] == 'exception'):
				raise Exception('requested exception')
			
	
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
	
	def get_delegate(self, req):
		"""
		@see: L{modu.web.app.resource.IResourceDelegate.get_delegate()}
		"""
		return TestResource()



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
		application.activate('/test-resource', TestResource)
		application.activate('/test-delegate', TestDelegateResource)


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
		application.activate('/test-resource', TestResource)
		application.activate('/test-delegate', TestDelegateResource)


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
		application.activate('/test-resource', TestResource)
		application.activate('/test-delegate', TestDelegateResource)


