# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

JQUERY_VERSION = '1.2.4'
JQUERY_UI_VERSION = '1.0'
JQUERY_PACKED = True
JQUERY_UI_PACKED = True

def get_jquery_path(req):
	if(JQUERY_PACKED):
		packed = '.pack'
	else:
		packed = ''
	return req.get_path('/assets/jquery/jquery-%s%s.js' % (JQUERY_VERSION, packed))

def get_jquery_ui_path(req, full=False):
	if(full):
		core = 'jquery.ui-all-%s' % JQUERY_UI_VERSION
	else:
		core = 'ui.core'
	
	if(JQUERY_UI_PACKED and JQUERY_UI_VERSION != '1.0'):
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, 'packed-javascript', core + '.packed.js')
	else:
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, '%s.js' % core)
	
	return url

def get_jquery_ui_component_path(req, module):
	if(JQUERY_UI_PACKED and JQUERY_UI_VERSION != '1.0'):
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, 'packed-javascript/%s.packed.js' % module)
	else:
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, '%s.js' % module)
	
	return url