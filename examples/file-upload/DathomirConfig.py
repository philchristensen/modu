from dathomir.config import handler
from dathomir import config, resource

from mod_python import util

import os

class MagicFile(file):
	def __init__(self, req, filename, mode='r', bufsize=-1):
		import tempfile, md5, os.path
		hashed_filename = os.path.join(tempfile.gettempdir(), md5.new(filename).hexdigest())
		
		super(MagicFile, self).__init__(hashed_filename, mode, bufsize)
		
		self.req = req
		self.client_filename = filename
		if('dathomir.file' not in req.session):
			self.req.session['dathomir.file'] = {}
		
		self.req.session['dathomir.file'][self.client_filename] = {'bytes_written':0, 'total_bytes':int(self.req.headers_in['Content-Length'])}
		self.req.session.save()
	
	def write(self, data):
		file_state = self.req.session['dathomir.file'][self.client_filename]
		file_state['bytes_written'] += len(data)
		self.req.session.save()
		super(MagicFile, self).write(data)
	
	def seek(self, offset, whence=0):
		self.req.session['dathomir.file'][self.client_filename]['complete'] = 1
		super(MagicFile, self).seek(offset, whence)

def magicFileHandler(req):
	def magicFileFactory(filename, mode='w+b', bufsize=-1):
		return MagicFile(req, filename, mode, bufsize)
	return magicFileFactory

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		if(req.tree.unparsed_path and req.tree.unparsed_path[0] == 'status'):
			if(len(req.tree.unparsed_path) >= 2):
				file_state = req.session['dathomir.file'][req.tree.unparsed_path[1]]
				if('complete' in file_state):
					self.add_slot('status', 'complete')
				else:
					self.add_slot('status', '%d/%d' % (file_state['bytes_written'], file_state['total_bytes']))
		else:
			forms = util.FieldStorage(req, file_callback=magicFileHandler(req))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		if(req.tree.unparsed_path and req.tree.unparsed_path[0] == 'status'):
			return 'status.html.tmpl'
		else:
			return 'page.html.tmpl'

config.base_path = '/dathomir/examples/file-upload'
config.initialize_store = False
config.activate(RootResource())
