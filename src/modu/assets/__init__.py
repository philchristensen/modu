# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

from modu.util import tags

# DEFAULT_JQUERY_VERSION = '1.11.0'
# DEFAULT_JQUERY_UI_VERSION = '1.9.2'
DEFAULT_JQUERY_VERSION = '1.4.2'
DEFAULT_JQUERY_UI_VERSION = '1.7.1'

def activate_jquery(req):
	req.content.report('header', tags.script(type="text/javascript", src="//code.jquery.com/jquery-%s.min.js" % DEFAULT_JQUERY_VERSION)[''])

def activate_jquery_ui(req):
	req.content.report('header', tags.script(type="text/javascript", src="//code.jquery.com/ui/%s/jquery-ui.min.js" % DEFAULT_JQUERY_UI_VERSION)[''])
