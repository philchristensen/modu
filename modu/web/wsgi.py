# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import urllib, os, threading

from twisted.internet import defer, threads
from twisted.web import resource, server, util
from twisted.python import log, failure


headerNameTranslation = ''.join([c.isalnum() and c.upper() or '_' for c in map(chr, range(256))])

def createCGIEnvironment(request):
	# See http://hoohoo.ncsa.uiuc.edu/cgi/env.html for CGI interface spec
	# http://cgi-spec.golux.com/draft-coar-cgi-v11-03-clean.html for a better one
	#remotehost = request.remoteAddr
	parts = request.received_headers['host'].split(':')
	serverName = parts[0]
	if(len(parts) > 1):
		requestPort = parts[1]
	else:
		requestPort = '80' #str(request.getHost().port)
	
	env = {} #dict(os.environ)
	# MUST provide:
	clength = request.received_headers.get('content-length', False)
	if clength:
		env["CONTENT_LENGTH"] = clength
	
	if('content-type' in request.received_headers):
		env["CONTENT_TYPE"] = request.received_headers['content-type']
	
	env["GATEWAY_INTERFACE"] = "CGI/1.1"
	
	# MUST always be present, even if no query
	qindex = request.uri.find('?')
	if qindex != -1:
		qs = env['QUERY_STRING'] = request.uri[qindex+1:]
		if '=' in qs:
			qargs = []
		else:
			qargs = [urllib.unquote(x) for x in qs.split('+')]
	else:
		env['QUERY_STRING'] = ''
		qargs = []
	
	#env["REMOTE_ADDR"] = remotehost.host
	client = request.getClient()
	if client is not None:
		env['REMOTE_HOST'] = client
	ip = request.getClientIP()
	if ip is not None:
		env['REMOTE_ADDR'] = ip
	
	env["REQUEST_METHOD"] = request.method
	# Should we raise an exception if this contains "/" chars?
	env["SCRIPT_NAME"] = '/'
	if request.prepath:
		env["SCRIPT_NAME"] += '/'.join(request.prepath)
		# print 'sn: ' + env['SCRIPT_NAME']
	
	env["PATH_INFO"] = '/'
	if request.postpath:
		env["PATH_INFO"] += '/'.join(request.postpath)
		# print 'pi: ' + env['PATH_INFO']
	
	env["SERVER_NAME"] = serverName
	env["SERVER_PORT"] = requestPort
	
	env["SERVER_PROTOCOL"] = request.clientproto
	env["SERVER_SOFTWARE"] = server.version
	
	# SHOULD provide
	# env["AUTH_TYPE"] # FIXME: add this
	# env["REMOTE_HOST"] # possibly dns resolve?
	
	# MAY provide
	# env["PATH_TRANSLATED"] # Completely worthless
	# env["REMOTE_IDENT"] # Completely worthless
	# env["REMOTE_USER"] # FIXME: add this
	
	# Unofficial, but useful and expected by applications nonetheless
	env["REMOTE_PORT"] = str(request.client.port)
	env["REQUEST_URI"] = request.uri
	
	scheme = ('http', 'https')[request.isSecure()]
	env["REQUEST_SCHEME"] = scheme
	env["HTTPS"] = ("off", "on")[scheme == "https"]
	env["SERVER_PORT_SECURE"] = ("0", "1")[scheme == "https"]
	
	# Propagate HTTP headers
	for title in request.received_headers:
		header = request.received_headers[title]
		envname = title.translate(headerNameTranslation)
		# Don't send headers we already sent otherwise, and don't
		# send authorization headers, because that's a security
		# issue.
		if title not in ('content-type', 'content-length',
						 'authorization', 'proxy-authorization'):
			envname = "HTTP_" + envname
		env[envname] = header
	
	for k,v in env.items():
		if type(k) is not str:
			print "is not string:",k
		if type(v) is not str:
			print k, "is not string:",v
	return env

class UnparsedRequest(server.Request):
	"""
	This Request subclass omits the request body parsing that
	happens before our code takes over. This lets us use the
	NestedFieldStorage (or alternative) to parse the body.
	"""
	def requestReceived(self, command, path, version):
		"""Called by channel when all data has been received.
		
		This method is not intended for users.
		"""
		self.content.seek(0,0)
		self.args = {}
		self.stack = []
		
		self.method, self.uri = command, path
		self.clientproto = version
		x = self.uri.split('?', 1)
		
		if len(x) == 1:
			self.path = self.uri
		else:
			self.path, argstring = x
			#self.args = parse_qs(argstring, 1)
		
		# cache the client and server information, we'll need this later to be
		# serialized and sent with the request so CGIs will work remotely
		self.client = self.channel.transport.getPeer()
		self.host = self.channel.transport.getHost()
		
		self.process()

class WSGIResource(resource.Resource):
	isLeaf = True
	
	def __init__(self, application, env=None):
		resource.Resource.__init__(self)
		self.application = application
		self.env = env
	
	def render(self, request):
		from twisted.internet import reactor
		# Do stuff with WSGIHandler.
		handler = WSGIHandler(self.application, request)
		if(self.env):
			for k, v in self.env.items():
				if(callable(v)):
					handler.environment[k] = v()
				else:
					handler.environment[k] = v
		handler.responseDeferred.addCallback(self._finish, request)
		handler.responseDeferred.addErrback(self._error, request)
		
		# Run it in a thread
		reactor.callInThread(handler.run)
		return server.NOT_DONE_YET
	
	def _finish(self, content, request):
		if(hasattr(content, 'read')):
			b = content.read(8192)
			while(b):
				request.write(b)
				b = content.read(8192)
		elif(isinstance(content, (list, tuple))):
			for item in content:
				request.write(item)
		
		request.finish()
	
	def _error(self, failure, request):
		content = util.formatFailure(failure)
		request.setHeader('Content-Type', 'text/html')
		request.setHeader('Content-Length', len(content))
		request.write(content)
		request.finish()
	

class AlreadyStartedResponse(Exception):
	pass

class ErrorStream(object):
	"""
	This class implements the 'wsgi.error' object.
	"""
	def flush(self):
		# Called in application thread
		return
	
	def write(self, s):
		# Called in application thread
		if(s.endswith('\n')):
			s = s[:-1]
		log.msg("[WSGI] "+s, isError=True)
	
	def writelines(self, seq):
		# Called in application thread
		s = ''.join(seq)
		log.msg("[WSGI] "+s, isError=True)

class WSGIHandler(object):
	headersSent = False
	stopped = False
	stream = None
	
	def __init__(self, application, request):
		# Called in IO thread
		self.setupEnvironment(request)
		self.application = application
		self.request = request
		#self.response = None
		self.started = False
		self.responseDeferred = defer.Deferred()
	
	def setupEnvironment(self, request):
		# Called in IO thread
		env = createCGIEnvironment(request)
		env['wsgi.version']      = (1, 0)
		env['wsgi.url_scheme']   = env['REQUEST_SCHEME']
		env['wsgi.input']        = request.content
		env['wsgi.errors']       = ErrorStream()
		env['wsgi.multithread']  = True
		env['wsgi.multiprocess'] = False
		env['wsgi.run_once']     = False
		env['wsgi.file_wrapper'] = FileWrapper
		
		self.environment = env
	
	def startWSGIResponse(self, status, response_headers, exc_info=None):
		# Called in application thread
		if exc_info is not None:
			try:
				if self.headersSent:
					raise exc_info[0], exc_info[1], exc_info[2]
			finally:
				exc_info = None
		elif self.started:
			raise AlreadyStartedResponse, 'startWSGIResponse(%r)' % status
		
		self.request.setResponseCode(int(status.split(' ')[0]))
		
		#self.response = http.Response(status)
		self.started = True
		for key, value in response_headers:
			#self.response.headers.addRawHeader(key, value)
			self.request.setHeader(key, value)
		
		return self.write
	
	def run(self):
		from twisted.internet import reactor
		# Called in application thread
		try:
			result = self.application(self.environment, self.startWSGIResponse)
			self.handleResult(result)
		except:
			if not self.headersSent:
				reactor.callFromThread(self.__error, failure.Failure())
			else:
				reactor.callFromThread(self.stream.finish, failure.Failure())
	
	def __callback(self, data=None):
		# Called in IO thread
		self.responseDeferred.callback(data)
		self.responseDeferred = None
	
	def __error(self, f):
		# Called in IO thread
		self.responseDeferred.errback(f)
		self.responseDeferred = None
	
	def write(self, output):
		# Called in application thread
		from twisted.internet import reactor
		if not self.started:
			raise RuntimeError(
				"Application didn't call startResponse before writing data!")
		if not self.headersSent:
			#self.stream=self.response.stream=stream.ProducerStream()
			self.headersSent = True
			
			# threadsafe event object to communicate paused state.
			self.unpaused = threading.Event()
			
			# After this, we cannot touch self.response from this
			# thread any more
			def _start():
				# Called in IO thread
				self.request.registerProducer(self, True)
				self.__callback()
				# Notify application thread to start writing
				self.unpaused.set()
			reactor.callFromThread(_start)
		# Wait for unpaused to be true
		self.unpaused.wait()
		reactor.callFromThread(self.request.write, output)
	
	def writeAll(self, result):
		# Called in application thread
		from twisted.internet import reactor
		if not self.headersSent:
			if not self.started:
				raise RuntimeError(
					"Application didn't call startResponse before writing data!")
			
			# for item in result:
			# 	self.request.write(item)
			# self.request.finish()
			reactor.callFromThread(self.__callback, result)
		else:
			# Has already been started, cannot replace the stream
			def _write():
				# Called in IO thread
				for s in result:
					self.request.write(s)
				self.request.finish()
			reactor.callFromThread(_write)
	
	def handleResult(self, result):
		# Called in application thread
		try:
			from twisted.internet import reactor
			if (isinstance(result, FileWrapper) and
				   hasattr(result.filelike, 'fileno') and
				   not self.headersSent):
				if not self.started:
					raise RuntimeError(
						"Application didn't call startResponse before writing data!")
				self.headersSent = True
				# Make FileStream and output it. We make a new file
				# object from the fd, just in case the original one
				# isn't an actual file object.
				# self.response.stream = stream.FileStream(
				# 	os.fdopen(os.dup(result.filelike.fileno())))
				reactor.callFromThread(self.__callback, 
					os.fdopen(os.dup(result.filelike.fileno())))
				return
			
			if type(result) in (list,tuple):
				# If it's a list or tuple (exactly, not subtype!),
				# then send the entire thing down to Twisted at once,
				# and free up this thread to do other work.
				self.writeAll(result)
				return
			
			# Otherwise, this thread has to keep running to provide the
			# data.
			for data in result:
				if self.stopped:
					return
				self.write(data)
			
			if not self.headersSent:
				if not self.started:
					raise RuntimeError(
						"Application didn't call startResponse, and didn't send any data!")
				
				self.headersSent = True
				reactor.callFromThread(self.__callback)
			else:
				reactor.callFromThread(self.request.finish)
			
		finally:
			if hasattr(result,'close'):
				result.close()
	
	def pauseProducing(self):
		# Called in IO thread
		self.unpaused.set()
	
	def resumeProducing(self):
		# Called in IO thread
		self.unpaused.clear()
	
	def stopProducing(self):
		self.stopped = True

class FileWrapper(object):
	"""
	Wrapper to convert file-like objects to iterables, to implement
	the optional 'wsgi.file_wrapper' object.
	"""
	
	def __init__(self, filelike, blksize=8192):
		self.filelike = filelike
		self.blksize = blksize
		if hasattr(filelike,'close'):
			self.close = filelike.close
	
	def __iter__(self):
		return self
	
	def next(self):
		data = self.filelike.read(self.blksize)
		if data:
			return data
		raise StopIteration
