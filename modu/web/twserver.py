# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import os
from twisted.web2 import server, channel, static, wsgi
from modu.web import app

class ModuWSGIResource(wsgi.WSGIResource):
	def renderHTTP(self, req):
		from twisted.internet import reactor
		# Do stuff with WSGIHandler.
		handler = wsgi.WSGIHandler(self.application, req)
		handler.environment['SCRIPT_FILENAME'] = os.getcwd()
		# Get deferred
		d = handler.responseDeferred
		# Run it in a thread
		reactor.callInThread(handler.run)
		return d


# This part gets run when you run this file via: "twistd -noy modu/web/twisted.py"
root = ModuWSGIResource(app.handler)
site = server.Site(root)

# Start up the server
from twisted.application import service, strports
application = service.Application("modu")
s = strports.service('tcp:8888', channel.HTTPFactory(site))
s.setServiceParent(application)