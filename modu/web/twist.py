# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import urllib, os, sys

from twisted.internet import defer
from twisted.web import resource, server, util
from twisted.web2 import wsgi, stream
from twisted.python import log

headerNameTranslation = ''.join([c.isalnum() and c.upper() or '_' for c in map(chr, range(256))])

# Python 2.4.2 (only) has a broken mmap that leaks a fd every time you call it.
if sys.version_info[0:3] != (2,4,2):
	try:
		import mmap
	except ImportError:
		mmap = None
else:
	mmap = None

def createCGIEnvironment(request):
	# See http://hoohoo.ncsa.uiuc.edu/cgi/env.html for CGI interface spec
	# http://cgi-spec.golux.com/draft-coar-cgi-v11-03-clean.html for a better one
	#remotehost = request.remoteAddr
	serverName = request.getRequestHostname().split(':')[0]
	python_path = os.pathsep.join(sys.path)
	
	env = {} #dict(os.environ)
	# MUST provide:
	clength = request.received_headers.get('content-length', False)
	if clength:
		env["CONTENT_LENGTH"] = clength
	
	if('content-type' in request.received_headers):
		env["CONTENT_TYPE"] = request.received_headers['content-type']
	
	env["GATEWAY_INTERFACE"] = "CGI/1.1"
	
	if request.postpath:
		# Should we raise an exception if this contains "/" chars?
		env["PATH_INFO"] = '/' + '/'.join(request.postpath)
	
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
	if request.prepath:
		env["SCRIPT_NAME"] = '/' + '/'.join(request.prepath)
	else:
		env["SCRIPT_NAME"] = ''
	
	env["SERVER_NAME"] = serverName
	env["SERVER_PORT"] = str(request.getHost().port)
	
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


class WSGIResource(resource.Resource):
	isLeaf = True
	
	def __init__(self, application):
		self.application = application
	
	def render(self, request):
		from twisted.internet import reactor
		# Do stuff with WSGIHandler.
		handler = WSGIHandler(self.application, request)
		handler.environment['SCRIPT_FILENAME'] = os.getcwd()
		
		handler.responseDeferred.addCallback(self._finish, request)
		handler.responseDeferred.addErrback(self._error, request)
		
		# Run it in a thread
		reactor.callInThread(handler.run)
		return server.NOT_DONE_YET
	
	def _write(self, content, request):
		request.write(content)
		request.finish()
	
	def _finish(self, response, request):
		request.setResponseCode(response.code)
		
		for key, values in response.headers.getAllRawHeaders():
			for value in values:
				request.setHeader(key, value)
		
		if(isinstance(response.stream, stream.FileStream)):
			response.stream.useMMap = False
			b = response.stream.read()
			while(b):
				request.write(b)
				b = response.stream.read()
			request.finish()
			return
		
		content = response.stream.read()
		if(isinstance(content, defer.Deferred)):
			content.addCallback(self._write, request)
		else:
			self._write(content, request)
	
	def _error(self, failure, request):
		content = util.formatFailure(failure)
		request.setHeader('Content-Type', 'text/html')
		request.setHeader('Content-Length', len(content))
		self._write(content, request)


class WSGIHandler(wsgi.WSGIHandler):
	def setupEnvironment(self, request):
		# Called in IO thread
		env = createCGIEnvironment(request)
		env['wsgi.version']      = (1, 0)
		env['wsgi.url_scheme']   = env['REQUEST_SCHEME']
		env['wsgi.input']        = request.content
		env['wsgi.errors']       = wsgi.ErrorStream()
		env['wsgi.multithread']  = True
		env['wsgi.multiprocess'] = False
		env['wsgi.run_once']     = False
		env['wsgi.file_wrapper'] = wsgi.FileWrapper
		
		self.environment = env

