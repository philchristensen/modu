# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Essential web application components.
"""

class HTTPStatus(Exception):
	"""
	An HTTPStatus exception can be thrown from anywhere within the
	modu architecture to change the final result of the request.
	"""
	def __init__(self, status, headers, content):
		self.status = status
		self.headers = headers
		if(isinstance(content, str)):
			self.content = [content]
		else:
			self.content = content
		
		Exception.__init__(self, ''.join(content))
	
	def get_content(self):
		return '\n'.join(self.content)

class MaintenanceMode(Exception):
	"""
	This error will be thrown when the server is in maintenance mode.
	"""

