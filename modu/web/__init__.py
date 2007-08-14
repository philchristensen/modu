# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Essential web application components.
"""

class HTTPStatus(Exception):
	def __init__(self, status, headers, content):
		self.status = status
		self.headers = headers
		self.content = content
		Exception.__init__(self, status)

