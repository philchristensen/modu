# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import traceback, mimetypes, os, stat, os.path

def handler(env, start_response):
	from modu.web import app
	
	req = get_request(env)
	
	result = check_file(req)
	if(result):
		content = []
		if(result[1]):
			app.add_header('Content-Type', result[1])
			app.add_header('Content-Length', result[2])
			try:
				content = FileWrapper(open(result[0]))
			except:
				status = '401 Forbidden'
			else:
				status = '200 OK'
		else:
			status = '401 Forbidden'
		start_response(status, app.get_headers())
		return content
	
	tree = app.get_tree()
	rsrc = tree.parse(req['modu.path'])
	if not(rsrc):
		start_response('404 Not Found', [])
		return []
	
	req['modu.tree'] = tree
	
	app.bootstrap(req)
	
	rsrc.prepare_content(req)
	app.add_header('Content-Type', rsrc.get_content_type(req))
	content = rsrc.get_content(req)
	app.add_header('Content-Length', len(content))
	
	if('modu.session' in req):
		req['modu.session'].save()
	
	start_response('200 OK', app.get_headers())
	return [content]

def check_file(req):
	true_path = req['PATH_TRANSLATED']
	try:
		finfo = os.stat(true_path)
		# note that there's no support for directory indexes,
		# only direct file access under the webroot
		if(stat.S_ISREG(finfo.st_mode)):
			try:
				content_type = mimetypes.guess_type(true_path)[0]
				size = finfo.st_size
				return (true_path, content_type, size)
			except IOError:
				return (true_path, None, None)
	except OSError:
		pass
	
	return None

def get_request(env):
	from modu.web import app
	app.load_config(env)
	
	# Hopefully the next release of mod_python
	# will let us ditch this line
	env['SCRIPT_NAME'] = env['modu.config.base_url']
	
	# once the previous line is gone, this next
	# block should be able to be moved elsewhere
	uri = env['REQUEST_URI']
	if(uri.startswith(env['SCRIPT_NAME'])):
		env['PATH_INFO'] = uri[len(env['SCRIPT_NAME']):]
	else:
		env['PATH_INFO'] = uri
	
	env['modu.approot'] = env['SCRIPT_FILENAME']
	env['modu.path'] = env['PATH_INFO']
	
	approot = env['modu.approot']
	webroot = env['modu.config.webroot']
	webroot = os.path.join(approot, webroot)
	env['PATH_TRANSLATED'] = os.path.realpath(webroot + env['modu.path'])
	
	return Request(env)

class FileWrapper:
	def __init__(self, filelike, blksize=8192):
		self.filelike = filelike
		self.blksize = blksize
		if hasattr(filelike,'close'):
			self.close = filelike.close
	
	def __getitem__(self,key):
		data = self.filelike.read(self.blksize)
		if data:
			return data
		raise IndexError

class Request(dict):
	"""
	At this point we are supposedly server-neutral, although
	the code does make a few assumptions about what various
	environment variables actually mean. Shocking.
	"""
	def __init__(self, env={}):
		dict.__init__(self)
		self.update(env)
	
	def __getattr__(self, key):
		if(key in self):
			return self[key]
		elif(key.find('_') != -1):
			return self[key.replace('_', '.')]
		raise AttributeError(key)
	
	def log_error(self, data):
		self['wsgi.errors'].write(data)
	
	def has_form_data(self):
		if(self['REQUEST_METHOD'] == 'POST'):
			return True
		elif(self['QUERY_STRING']):
			return True
		return False

