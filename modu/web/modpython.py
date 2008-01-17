# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from mod_python import apache
from modu.web import app

def handler(mp_req):
	"""
	The ModPython handler. This will create the necessary
	environment dictionary, hand off to the WSGI handler,
	and return the results of the WSGI subsystem.
	"""
	req = get_wsgi_environment(mp_req)
	req['modpython.request'] = mp_req
	
	def start_response(status, response_headers):
		mp_req.status = int(status[:3])
		
		import os, time
		mp_req.log_error('%d - %f - %s - %s' % (os.getpid(), time.time(), req['REQUEST_URI'], status))
		
		for key, val in response_headers:
			if key.lower() == 'content-length':
				mp_req.set_content_length(long(val))
			elif key.lower() == 'content-type':
				mp_req.content_type = val
			else:
				mp_req.headers_out.add(key, val)
		
		return mp_req.write
	
	content = app.handler(req, start_response)
	if(isinstance(content, FileWrapper)):
		mp_req.sendfile(content.filelike.name)
		if(hasattr(content, 'close')):
			content.close()
	else:
		for data in content:
			mp_req.write(data)
	return apache.OK

def get_wsgi_environment(mp_req):
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
	
	env = dict(apache.sql.build_cgi_env(mp_req))
	
	# We'll set MODU_ENV, but SCRIPT_NAME will
	# be misleading until the modu app code actually
	# gets started. The next release of mod_python
	# should be adding mp_req.hlist['location'],
	# which will fix this.
	#env['SCRIPT_NAME'] = mp_req.hlist['location']
	env['MODU_ENV'] = apache.get_handler_root()
	
	if('CONTENT_LENGTH' in mp_req.headers_in):
		env['CONTENT_LENGTH'] = long(mp_req.headers_in['Content-Length'])
	
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

class FileWrapper:
	"""
	Standard WSGI filewrapper. The mod_python WSGI gateway knows
	to recognize this class and use sendfile on its filelike object
	instead of handling it internally.
	"""
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

class InputWrapper(object):
	"""
	Mod_Python input wrapper for WSGI.
	"""
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
	"""
	Mod_Python error wrapper for WSGI.
	"""
	def __init__(self, mp_req):
		self.mp_req = mp_req
	
	def flush(self):
		pass
	
	def write(self, msg):
		self.mp_req.log_error(msg)
	
	def writelines(self, seq):
		self.write(''.join(seq))

