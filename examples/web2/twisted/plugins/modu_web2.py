# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Unsupported Twisted plugin to launch a modu web application container.

Due to the nature of web2, this plugin is only provided as a reference.
"""

import os

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import service, strports
from twisted.internet import reactor
from twisted.web2 import server, channel, wsgi

from modu.web import app

class Options(usage.Options):
	"""
	Implement usage parsing for the modu-web plugin.
	"""
	optParameters = [["port", "p", 8888, "Port to use for web server."]
					]


class ModuwWeb2WSGIResource(wsgi.WSGIResource):
	"""
	This simple subclass sets env['SCRIPT_FILENAME'] to the current directory.
	"""
	def renderHTTP(self, req):
		# Do stuff with WSGIHandler.
		handler = wsgi.WSGIHandler(self.application, req)
		handler.environment['SCRIPT_FILENAME'] = os.getcwd()
		# Get deferred
		d = handler.responseDeferred
		# Run it in a thread
		reactor.callInThread(handler.run)
		return d


class ModuWeb2ServiceMaker(object):
	"""
	Create a modu web service with twisted.web.
	"""
	implements(service.IServiceMaker, IPlugin)
	tapname = "modu-web2"
	description = "Run a modu application server."
	options = Options
	
	def makeService(self, config):
		"""
		Instantiate the service.
		"""
		root = ModuwWeb2WSGIResource(app.handler)
		site = server.Site(root)
		
		s = strports.service('tcp:' + str(config['port']), channel.HTTPFactory(site))
		
		return s


serviceMaker = ModuWeb2ServiceMaker()