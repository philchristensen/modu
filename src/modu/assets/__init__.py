# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

from modu.util import tags

DEFAULT_JQUERY_VERSION = '1.11.0'
DEFAULT_JQUERY_UI_VERSION = '1.9.2'

def activate_jquery(req):
	req.content.report('header', tags.script(type="text/javascript", src="//ajax.googleapis.com/ajax/libs/jquery/%s/jquery.min.js" % DEFAULT_JQUERY_VERSION)[''])

def activate_jquery_ui(req):
	req.content.report('header', tags.script(type="text/javascript", src="//ajax.googleapis.com/ajax/libs/jqueryui/%s/jquery-ui.min.js" % DEFAULT_JQUERY_UI_VERSION)[''])
