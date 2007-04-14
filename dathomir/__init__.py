#!/usr/bin/python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

try:
	from mod_python import apache

	def handler(request):
		request.content_type = "text/plain"
		request.write("Hello World! Again.")
		return apache.OK
except:
	pass