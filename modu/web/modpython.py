# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from mod_python import apache
from modu.web import wsgi, app

def handler(mp_req):
	"""
	The ModPython handler. This will create the necessary
	environment dictionary, hand off to the WSGI handler,
	and return the results of the WSGI subsystem.
	"""
	req = wsgi.get_environment(mp_req)
	
	def start_response(status, response_headers):
		mp_req.status = int(status[:3])
		
		for key, val in app.get_headers():
			if key.lower() == 'content-length':
				mp_req.set_content_length(long(val))
			elif key.lower() == 'content-type':
				mp_req.content_type = val
			else:
				mp_req.headers_out.add(key, val)
		
		return mp_req.write
	
	content = wsgi.handler(req, start_response)
	if(isinstance(content, wsgi.FileWrapper)):
		mp_req.sendfile(content.filelike.name)
	else:
		for data in content:
			mp_req.write(data)
	return apache.OK

