# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import internet, service
from twisted.internet import reactor
from twisted.web import server, resource

from modu.web import twist, app

import os

app.try_lucene_threads()

class Options(usage.Options):
	optParameters = [["port", "p", 8888, "Port to use for web server."]
					]

class ModuServiceMaker(object):
	implements(service.IServiceMaker, IPlugin)
	tapname = "modu-web"
	description = "Run a modu application server."
	options = Options
	
	def makeService(self, config):
		site = server.Site(twist.WSGIResource(app.handler))
		web_service = internet.TCPServer(int(config['port']), site)
		
		return web_service

serviceMaker = ModuServiceMaker()