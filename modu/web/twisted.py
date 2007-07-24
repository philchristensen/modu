# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.web2 import server, channel, static, wsgi
from modu.web import app

"""
PARTIALLY BROKEN

At least partially. Apart from the fact that I haven't even run this code
because web2 doesn't wish to be found right now, the only way a site can
be registered is to add an ISite plugin to the global plugin path.
"""

class ModuWSGIResource(wsgi.WSGIResource):
	def renderHTTP(self, req):
		from twisted.internet import reactor
		# Do stuff with WSGIHandler.
		handler = WSGIHandler(self.application, req)
		# Get deferred
		d = handler.responseDeferred
		# Run it in a thread
		reactor.callInThread(handler.run)
		return d


# This part gets run when you run this file via: "twistd -noy modu/web/twisted.py"
root = wsgi.WSGIResource(app.handler)
site = server.Site(root)

# Start up the server
from twisted.application import service, strports
application = service.Application("modu")
s = strports.service('tcp:8888', channel.HTTPFactory(site))
s.setServiceParent(application)