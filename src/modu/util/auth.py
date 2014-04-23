# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

import base64

from modu.web import app, user

def request_basic(req, message=None, realm_name='Secure Area'):
	req.add_header('WWW-Authenticate', 'Basic realm="%s"' % realm_name)
	app.raise401(message)

def has_basic(req):
	auth_header = req.get('HTTP_AUTHORIZATION', '').strip()
	if(auth_header.lower().startswith('basic')):
		return True
	
	return False

def verify_basic(req, use_session=False):
	auth_header = req.get('HTTP_AUTHORIZATION', '').strip()
	try:
		method, token = auth_header.split()
	except:
		req.log_error('Invalid authorization header: %r' % auth_header)
		return None
	
	if(method.lower() != 'basic'):
		return None
	
	try:
		username, password = base64.b64decode(token).split(':')
	except:
		req.log_error('Invalid authorization token: %r' % token)
		return None
	
	u = user.authenticate_user(req, username, password)
	
	if(use_session):
		req.session.set_user(u)
	
	return u