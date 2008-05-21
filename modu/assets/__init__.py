# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def get_jquery_path(req):
	return req.get_path('/assets/jquery/jquery-1.2.4.pack.js')

def get_jquery_ui_path(req, module):
	pass