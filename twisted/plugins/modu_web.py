# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Twisted plugin to launch a modu web application container.
"""

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application import internet, service
from twisted.internet import reactor
from twisted.web import server, resource

from modu.web import wsgi, app

import os

class Options(usage.Options):
	"""
	Implement usage parsing for the modu-web plugin.
	"""
	optParameters = [["port", "p", 8888, "Port to use for web server."],
					 ['logfile', 'l', 'twistd-access.log', 'Path to access log.']
					]

class ModuServiceMaker(object):
	"""
	Create a modu web service with twisted.web.
	"""
	implements(service.IServiceMaker, IPlugin)
	tapname = "modu-web"
	description = "Run a modu application server."
	options = Options
	
	def makeService(self, config):
		"""
		Instantiate the service.
		"""
		if(config['logfile'] != '-'):
			site = server.Site(wsgi.WSGIResource(app.handler), logPath=config['logfile'])
		else:
			site = server.Site(wsgi.WSGIResource(app.handler))
		server.Site.requestFactory = app.UnparsedRequest
		
		web_service = internet.TCPServer(int(config['port']), site)
		
		return web_service

serviceMaker = ModuServiceMaker()