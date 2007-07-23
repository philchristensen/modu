# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import resource
from modu.web.app import ISite

from zope.interface import classProvides
from twisted import plugin

import os

class SabiDefaultSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, app):
		app.base_domain = 'localhost:8888'
		app.base_path = '/modu/examples/sabi'
		self.load_plugins(app)
	
	def load_plugins(self, app):
		# import modu.sabi.plugins
		# reload(modu.sabi.plugins)
		# 
		# for site_plugin in plugin.getPlugins(plugin.ISabiPlugin, modu.sabi.plugins):
		# 	app.activate(site_plugin(app))
		pass