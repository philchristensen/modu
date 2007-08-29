# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import stat, mimetypes, os.path

from zope.interface import implements

from modu.web import resource

def get_file_essentials(req, path):
	from modu.web import app
	
	finfo = os.stat(path)
	# note that there's no support for directory indexes,
	# only direct file access under the webroot
	if(stat.S_ISREG(finfo.st_mode)):
		from modu.web import app
		if(not app.mimetypes_init and req.app.magic_mime_file):
			mimetypes.init([req.app.magic_mime_file])
		content_type = mimetypes.guess_type(path, False)[0]
		if(content_type is None):
			content_type = 'application/octet-stream'
		size = finfo.st_size
		return (content_type, size)
	else:
		return None

class FileResource(object):
	implements(resource.IResource, resource.IResourceDelegate)
	
	def __init__(self, paths, root, alternate=None):
		self.paths = paths
		self.alternate = alternate
		self.root = root
	
	def get_response(self, req):
		req.app.add_header('Content-Type', self.content_type)
		req.app.add_header('Content-Length', self.size)
		file_wrapper = req['wsgi.file_wrapper']
		return file_wrapper(open(self.true_path))
	
	def get_delegate(self, req):
		self.content_type = None
		self.size = None
		self.true_path = os.path.join(self.root, '/'.join(req.app.tree.postpath))
		
		try:
			self.content_type, self.size = get_file_essentials(req, self.true_path)
		except IOError:
			app.raise403('Cannot discern type: %s' % req['REQUEST_URI'])
		except (TypeError, OSError):
			return self._return_alternate(req)
		
		return self
	
	def _return_alternate(self, req):
		if(self.alternate):
			return self.alternate
		from modu.web import app
		app.raise404(req['REQUEST_URI'])
	
	def get_paths(self):
		return self.paths

