# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

JQUERY_VERSION = '1.2.6'
JQUERY_UI_VERSION = '1.5b4'
JQUERY_PACKED = True
JQUERY_UI_PACKED = True

def get_jquery_path(req, packed=JQUERY_PACKED):
	if(packed):
		packed = '.pack'
	else:
		packed = ''
	return req.get_path('/assets/jquery/jquery-%s%s.js' % (JQUERY_VERSION, packed))

def get_jquery_ui_path(req, full=False, packed=JQUERY_UI_PACKED):
	if(full):
		core = 'jquery.ui-all-%s' % JQUERY_UI_VERSION
	else:
		core = 'ui.core'
	
	if(packed and JQUERY_UI_VERSION != '1.0'):
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, 'packed-javascript', core + '.packed.js')
	else:
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, '%s.js' % core)
	
	return url

def get_jquery_ui_component_path(req, module, packed=JQUERY_UI_PACKED):
	if(packed and JQUERY_UI_VERSION != '1.0'):
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, 'packed-javascript/%s.packed.js' % module)
	else:
		url = req.get_path('/assets/jquery/jquery.ui-%s' % JQUERY_UI_VERSION, '%s.js' % module)
	
	return url
