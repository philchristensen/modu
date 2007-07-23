# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.web import app, resource
from modu.util import form

from modu.web.app import ISite
from zope.interface import classProvides
from twisted import plugin

import os, time, urllib

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		tree = req['modu.tree']
		session = req['modu.session']
		if(tree.unparsed_path):
			if(tree.unparsed_path[0] == 'status' and len(tree.unparsed_path) >= 2):
				selected_file = urllib.unquote(tree.unparsed_path[1])
				if('modu.file' in session):
					info_dict = session['modu.file']
					if(selected_file in info_dict):
						file_state = info_dict.setdefault(selected_file, {})
						if('complete' in file_state):
							self.set_slot('status', 'complete')
							del session['modu.file'][selected_file]['bytes_written']
						else:
							written = file_state.get('bytes_written', 0)
							total = file_state.get('total_bytes', 1)
							self.set_slot('status', '%s/%s' % (written, total))
					else:
						self.set_slot('status', '0/1')
				else:
					self.set_slot('status', '0/1')
		else:
			forms = form.NestedFieldStorage(req)
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		tree = req['modu.tree']
		if(tree.unparsed_path and tree.unparsed_path[0] == 'status'):
			return 'status.html.tmpl'
		else:
			return 'page.html.tmpl'

class FileUploadSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, application):
		application.base_domain = 'localhost:8888'
		application.base_path = '/modu/examples/file-upload'
		application.initialize_store = False
		#application.debug_session = True
		application.disable_session_users = True
		application.activate(RootResource())
