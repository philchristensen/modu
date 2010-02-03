# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import stat, mimetypes, os.path, urllib, time

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
		return (content_type, finfo)
	else:
		return None

class FileResource(object):
	implements(resource.IResource, resource.IResourceDelegate)
	
	def __init__(self, root, alternate=None, log_missing_files=True):
		self.alternate = alternate
		self.root = root
		self.log_missing_files = log_missing_files
	
	def get_response(self, req):
		req.add_header('Content-Type', self.content_type)
		req.add_header('Content-Length', self.finfo.st_size)
		
		if(req.app.config.get('static_file_caching', True)):
			req.add_header('Last-Modified', time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(self.finfo.st_mtime)))
			req.add_header('ETag', '%d/%d/%d' % (self.finfo.st_ino, self.finfo.st_mtime, self.finfo.st_size))

		file_wrapper = req['wsgi.file_wrapper']
		return file_wrapper(open(self.true_path))
	
	def get_delegate(self, req):
		self.content_type = None
		self.size = None
		self.true_path = os.path.join(self.root, '/'.join([urllib.unquote(x) for x in req.postpath]))
		
		try:
			self.content_type, finfo = get_file_essentials(req, self.true_path)
			self.finfo = finfo
		except IOError:
			app.raise403('Cannot discern type: %s' % req['REQUEST_URI'])
		except (TypeError, OSError):
			rsrc = self._return_alternate(req)
			return rsrc[0](*rsrc[1], **rsrc[2])
		
		return self
	
	def _return_alternate(self, req):
		if(self.alternate):
			return self.alternate
		if(self.log_missing_files):
			req.log_error('File does not exist: %s' % self.true_path)
		from modu.web import app
		app.raise404(req['REQUEST_URI'])


