from dathomir.config import handler
from dathomir import config, resource

from mod_python import util

import os, tempfile

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		if(req.tree.unparsed_path):
			if(req.tree.unparsed_path[0] == 'status'):
				self.add_slot('bytes', req.session['dathomir.file']['bytes_written'])
		else:
			forms = util.FieldStorage(req, file_callback=self.get_progressive_upload_handler(req))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		if(req.tree.unparsed_path and req.tree.unparsed_path[0] == 'status'):
			return 'status.html.tmpl'
		else:
			return 'page.html.tmpl'
	
	def get_progressive_upload_handler(self, req):
		class _upload_handler(file):
			def __init__(self, filename):
				file.__init__(self, filename)
				req.session['dathomir.file'] = {'bytes_written':0}
			
			def write(self, data):
				req.session['dathomir.file']['bytes_written'] += len(data)
				file.write(self, data)
		
		return _upload_handler

config.base_path = '/dathomir/examples/file-upload'
config.initialize_store = False
config.activate(RootResource())
