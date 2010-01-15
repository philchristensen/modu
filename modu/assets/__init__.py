# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import tags

DEFAULT_JQUERY_VERSION = '1.4'
DEFAULT_JQUERY_UI_VERSION = '1.7.1'
DEFAULT_JQUERY_MIN = False
DEFAULT_JQUERY_UI_MIN = True

def activate_google_jsapi(req):
	req.content.report('header', tags.script(type="text/javascript", src="http://www.google.com/jsapi")[''])

def activate_jquery(req):
	activate_google_jsapi(req)
	
	version = req.app.config.get('jquery_version', DEFAULT_JQUERY_VERSION)
	uncompressed = not req.app.config.get('jquery_compressed', DEFAULT_JQUERY_MIN)
	
	uncompressed = str(uncompressed).lower()
	
	req.content.report('header', tags.script(type="text/javascript")[
		'google.load("jquery","%s",{uncompressed:%s});' % (version, uncompressed)
	])

def activate_jquery_ui(req):
	activate_jquery(req)
	
	version = req.app.config.get('jquery_ui_version', DEFAULT_JQUERY_UI_VERSION)
	uncompressed = not req.app.config.get('jquery_ui_compressed', DEFAULT_JQUERY_UI_MIN)
	
	uncompressed = str(uncompressed).lower()
	
	req.content.report('header', tags.script(type="text/javascript")[
		'google.load("jqueryui", "%s", {uncompressed:%s});' % (version, uncompressed)
	])
