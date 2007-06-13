"""
WSGI wrapper for mod_python. Requires Python 2.2 or greater.


Example httpd.conf section for a CherryPy app called "mcontrol":

<Location /mcontrol>
	SetHandler python-program
	PythonFixupHandler mcontrol.cherry::startup
	PythonHandler modpython_gateway::handler
	PythonOption wsgi.application cherrypy._cpwsgi::wsgiApp
</Location>

Some WSGI implementations assume that the SCRIPT_NAME environ variable will
always be equal to "the root URL of the app"; Apache probably won't act as
you expect in that case. You can add another PythonOption directive to tell
modpython_gateway to force that behavior:

	PythonOption SCRIPT_NAME /mcontrol

Some WSGI applications need to be cleaned up when Apache exits. You can
register a cleanup handler with yet another PythonOption directive:

	PythonOption wsgi.cleanup module::function

The module.function will be called with no arguments on server shutdown,
once for each child process or thread.
"""

import traceback

from mod_python import apache

class InputWrapper(object):
	def __init__(self, req):
		self.req = req
	
	def close(self):
		pass
	
	def read(self, size=-1):
		return self.req.read(size)
	
	def readline(self, size=-1):
		return self.req.readline(size)
	
	def readlines(self, hint=-1):
		return self.req.readlines(hint)
	
	def __iter__(self):
		line = self.readline()
		while line:
			yield line
			# Notice this won't prefetch the next line; it only
			# gets called if the generator is resumed.
			line = self.readline()

class ErrorWrapper(object):
	def __init__(self, req):
		self.req = req
	
	def flush(self):
		pass
	
	def write(self, msg):
		self.req.log_error(msg)
	
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

def get_environment(req):
	options = req.get_options()
	
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
	
	env = dict(apache.build_cgi_env(req))
	
	if 'SCRIPT_NAME' in options:
		# Override SCRIPT_NAME and PATH_INFO if requested.
		env['SCRIPT_NAME'] = options['SCRIPT_NAME']
		env['PATH_INFO'] = req.uri[len(options['SCRIPT_NAME']):]
	
	env['wsgi.input'] = InputWrapper(req)
	env['wsgi.errors'] = ErrorWrapper(req)
	env['wsgi.file_wrapper'] = FileWrapper
	env['wsgi.version'] = (1,0)
	env['wsgi.run_once'] = False
	if env.get("HTTPS") in ('yes', 'on', '1'):
		env['wsgi.url_scheme'] = 'https'
	else:
		env['wsgi.url_scheme'] = 'http'
	env['wsgi.multithread']	 = threaded
	env['wsgi.multiprocess'] = forked
	
	return env

