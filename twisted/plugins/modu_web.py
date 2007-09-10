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
	optParameters = [["port", "p", 8888, "Port to use for web server."],
					 ['logfile', 'l', 'twistd-access.log', 'Path to access log.']
					]

class UnparsedRequest(server.Request):
	"""
	This Request subclass omits the request body parsing that
	happens before our code takes over. This lets us use the
	NestedFieldStorage (or alternative) to parse the body.
	"""
	def requestReceived(self, command, path, version):
		"""Called by channel when all data has been received.
		
		This method is not intended for users.
		"""
		self.content.seek(0,0)
		self.args = {}
		self.stack = []
		
		self.method, self.uri = command, path
		self.clientproto = version
		x = self.uri.split('?', 1)
		
		if len(x) == 1:
			self.path = self.uri
		else:
			self.path, argstring = x
			#self.args = parse_qs(argstring, 1)
		
		# cache the client and server information, we'll need this later to be
		# serialized and sent with the request so CGIs will work remotely
		self.client = self.channel.transport.getPeer()
		self.host = self.channel.transport.getHost()
		
		self.process()


class ModuServiceMaker(object):
	implements(service.IServiceMaker, IPlugin)
	tapname = "modu-web"
	description = "Run a modu application server."
	options = Options
	
	def makeService(self, config):
		server.Site.requestFactory = UnparsedRequest
		
		if(config['logfile'] != '-'):
			site = server.Site(twist.WSGIResource(app.handler), logPath=config['logfile'])
		else:
			site = server.Site(twist.WSGIResource(app.handler))
		
		web_service = internet.TCPServer(int(config['port']), site)
		
		return web_service

serviceMaker = ModuServiceMaker()