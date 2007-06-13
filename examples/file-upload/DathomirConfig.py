# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.app import handler
from dathomir import app, resource

from mod_python import util

import os, time

class MagicFile(file):
	def __init__(self, req, filename, mode='r', bufsize=-1):
		import tempfile, md5, os.path
		hashed_filename = os.path.join(tempfile.gettempdir(), md5.new(filename + time.ctime()).hexdigest())
		
		super(MagicFile, self).__init__(hashed_filename, mode, bufsize)
		
		self.req = req
		self.client_filename = filename
		if('dathomir.file' not in req.session):
			self.req.session['dathomir.file'] = {}
		
		byte_estimate = int(self.req.headers_in['Content-Length'])
		self.req.session['dathomir.file'][self.client_filename] = {'bytes_written':0, 'total_bytes':byte_estimate}
		self.req.session.save()
	
	def write(self, data):
		file_state = self.req.session['dathomir.file'][self.client_filename]
		file_state['bytes_written'] += len(data)
		self.req.session.save()
		super(MagicFile, self).write(data)
	
	def seek(self, offset, whence=0):
		self.req.log_error('file was sought')
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
		if(req.tree.unparsed_path and req.tree.unparsed_path[0] == 'status' and len(req.tree.unparsed_path) >= 2):
				selected_file = req.tree.unparsed_path[1]
				info_dict = req.session.setdefault('dathomir.file', {})
				file_state = info_dict.setdefault(selected_file, {})
				if('complete' in file_state):
					self.add_slot('status', 'complete')
					del req.session['dathomir.file'][selected_file]
				else:
					written = file_state.setdefault('bytes_written', 0)
					total = file_state.setdefault('total_bytes', 0)
					self.add_slot('status', '%d/%d' % (written, total))
		else:
			forms = util.FieldStorage(req, file_callback=magicFileHandler(req))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		if(req.tree.unparsed_path and req.tree.unparsed_path[0] == 'status'):
			return 'status.html.tmpl'
		else:
			return 'page.html.tmpl'

app.base_url = '/dathomir/examples/file-upload'
app.initialize_store = False
app.activate(RootResource())
