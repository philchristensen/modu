# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.app import handler
from dathomir import app, resource
from dathomir.util import form

import os, time

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		tree = req['dathomir.tree']
		session = req['dathomir.session']
		if(tree.unparsed_path and tree.unparsed_path[0] == 'status' and len(tree.unparsed_path) >= 2):
				selected_file = tree.unparsed_path[1]
				info_dict = session.setdefault('dathomir.file', {})
				file_state = info_dict.setdefault(selected_file, {})
				if('complete' in file_state):
					self.add_slot('status', 'complete')
					del session['dathomir.file'][selected_file]
				else:
					written = file_state.setdefault('bytes_written', 0)
					total = file_state.setdefault('total_bytes', 0)
					self.add_slot('status', '%d/%d' % (written, total))
		else:
			forms = form.NestedFieldStorage(req)
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		tree = req['dathomir.tree']
		if(tree.unparsed_path and tree.unparsed_path[0] == 'status'):
			return 'status.html.tmpl'
		else:
			return 'page.html.tmpl'

app.base_url = '/dathomir/examples/file-upload'
app.initialize_store = False
app.activate(RootResource())
