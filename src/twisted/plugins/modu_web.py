# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
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
from twisted.web import server, resource, wsgi

from modu.web import app
from modu.persist import dbapi

import os

class Options(usage.Options):
	"""
	Implement usage parsing for the modu-web plugin.
	"""
	optParameters = [["port", "p", 8888, "Port to use for web server.", int],
					 ['interface', 'i', '', 'Interface to listen on.'],
					 ['logfile', 'l', None, 'Path to access log.']
					]
	
	optFlags =		[["debug-db", "d", "Turn on dbapi debugging."]
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
		dbapi.debug = config['debug-db']
		
		wsgi_rsrc = wsgi.WSGIResource(reactor, reactor.getThreadPool(), app.handler)
		site = server.Site(wsgi_rsrc, logPath=config['logfile'])
		web_service = internet.TCPServer(config['port'], site, interface=config['interface'])
		
		return web_service

serviceMaker = ModuServiceMaker()