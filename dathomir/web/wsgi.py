# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import traceback, mimetypes, os, stat, os.path

from mod_python import apache

class Request(dict):
	def __init__(self, d):
		dict.__init__(self)
		self.update(d)
	
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

class InputWrapper(object):
	def __init__(self, mp_req):
		self.mp_req = mp_req
	
	def close(self):
		pass
	
	def read(self, size=-1):
		return self.mp_req.read(size)
	
	def readline(self, size=-1):
		return self.mp_req.readline(size)
	
	def readlines(self, hint=-1):
		return self.mp_req.readlines(hint)
	
	def __iter__(self):
		line = self.readline()
		while line:
			yield line
			# Notice this won't prefetch the next line; it only
			# gets called if the generator is resumed.
			line = self.readline()

class ErrorWrapper(object):
	def __init__(self, mp_req):
		self.mp_req = mp_req
	
	def flush(self):
		pass
	
	def write(self, msg):
		self.mp_req.log_error(msg)
	
	def writelines(self, seq):
		self.write(''.join(seq))

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

def get_environment(mp_req):
	options = mp_req.get_options()
	
	# Threading and forking
	try:
		q = apache.mpm_query
		threaded = q(apache.AP_MPMQ_IS_THREADED)
		forked = q(apache.AP_MPMQ_IS_FORKED)
	except AttributeError:
		threaded = options.get('multithread', '').lower()
		if threaded == 'on':
			threaded = True
		elif threaded == 'off':
			threaded = False
		else:
			raise ValueError(bad_value % "multithread")
		
		forked = options.get('multiprocess', '').lower()
		if forked == 'on':
			forked = True
		elif forked == 'off':
			forked = False
		else:
			raise ValueError(bad_value % "multiprocess")
	
	env = dict(apache.build_cgi_env(mp_req))
	
	from dathomir.web import app
	app.load_config(env)
	
	env['SCRIPT_FILENAME'] = env['dathomir.approot'] = apache.get_handler_root()
	env['SCRIPT_NAME'] = env['dathomir.config.base_url']
	
	uri = env['REQUEST_URI']
	if(uri.startswith(env['SCRIPT_NAME'])):
		env['PATH_INFO'] = env['dathomir.path'] = uri[len(env['SCRIPT_NAME']):]
	else:
		env['PATH_INFO'] = env['dathomir.path'] = uri
	
	if('CONTENT_LENGTH' in mp_req.headers_in):
		env['CONTENT_LENGTH'] = long(mp_req.headers_in['Content-Length'])
	
	approot = env['dathomir.approot']
	webroot = env['dathomir.config.webroot']
	webroot = os.path.join(approot, webroot)
	env['PATH_TRANSLATED'] = os.path.realpath(webroot + env['dathomir.path'])
	
	env['wsgi.input'] = InputWrapper(mp_req)
	env['wsgi.errors'] = ErrorWrapper(mp_req)
	env['wsgi.file_wrapper'] = FileWrapper
	env['wsgi.version'] = (1,0)
	env['wsgi.run_once'] = False
	if env.get("HTTPS") in ('yes', 'on', '1'):
		env['wsgi.url_scheme'] = 'https'
	else:
		env['wsgi.url_scheme'] = 'http'
	env['wsgi.multithread'] = threaded
	env['wsgi.multiprocess'] = forked
	
	return env

def handler(req, start_response):
	from dathomir.web import app
	
	req = Request(req)
	
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
	rsrc = tree.parse(req['dathomir.path'])
	if not(rsrc):
		start_response('404 Not Found', [])
		return []
	
	req['dathomir.tree'] = tree
	
	app.bootstrap(req)
	
	rsrc.prepare_content(req)
	app.add_header('Content-Type', rsrc.get_content_type(req))
	content = rsrc.get_content(req)
	app.add_header('Content-Length', len(content))
	
	if('dathomir.session' in req):
		req['dathomir.session'].save()
	
	start_response('200 OK', app.get_headers())
	return [content]

def check_file(req):
	true_path = req['PATH_TRANSLATED']
	try:
		finfo = os.stat(true_path)
		# note that there's no support for directory indexes,
		# only direct file access
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


