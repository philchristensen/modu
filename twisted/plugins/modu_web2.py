# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import service, strports
from twisted.internet import reactor
from twisted.web2 import server, channel, wsgi

from modu.web import app

class ModuwWeb2WSGIResource(wsgi.WSGIResource):
	def renderHTTP(self, req):
		# Do stuff with WSGIHandler.
		handler = wsgi.WSGIHandler(self.application, req)
		handler.environment['SCRIPT_FILENAME'] = os.getcwd()
		# Get deferred
		d = handler.responseDeferred
		# Run it in a thread
		reactor.callInThread(handler.run)
		return d


class Options(usage.Options):
	optParameters = [["port", "p", 8888, "Port to use for web server."]
					]


class ModuWeb2ServiceMaker(object):
	implements(service.IServiceMaker, IPlugin)
	tapname = "modu-web2"
	description = "Run a modu application server."
	options = Options
	
	def makeService(self, config):
		root = ModuwWeb2WSGIResource(app.handler)
		site = server.Site(root)
		
		s = strports.service('tcp:' + str(config['port']), channel.HTTPFactory(site))
		
		return s


serviceMaker = ModuWeb2ServiceMaker()