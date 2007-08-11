# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted import plugin

from zope.interface import classProvides

from modu.web import app

class BasicTestSite(object):
	classProvides(plugin.IPlugin, app.ISite)
	
	def initialize(self, application):
		application.base_domain = '____test-domain____:1234567'
		application.base_path = '/app-test'
		application.db_url = None
		application.session_class = None
		application.initialize_store = False


