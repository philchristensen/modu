# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

from modu import assets
from modu.util import tags

class ProgressBar(object):
	def __init__(self, req, value=0.0, maxvalue=1.0, callback_url=None, interval=5000, **attribs):
		self.req = req
		self.value = value
		self.maxvalue = maxvalue
		self.callback_url = callback_url
		self.interval = interval
		self.attribs = attribs
	
	def render(self):
		self.req.content.report('header', tags.style(type='text/css')[
			"@import '%s';" % self.req.get_path('assets/progress-bar/style.css')
		])
	
		assets.activate_jquery(self.req)
		
		self.req.content.report('header', tags.script(type='text/javascript',
			src=self.req.get_path('assets/progress-bar/support.js'))[''])
	
		element_id = self.attribs.get('element_id', 'progress-bar')
		attribs = self.attribs.copy()
		attribs.pop('element_id', None)
	
		content = tags.div(_id=element_id, _class='progress-field', **attribs)[[
			tags.div(_class='progress-bar')[''],
			tags.div(_class='progress-text')['']
		]]
		
		if(self.callback_url):
			content += tags.script(type='text/javascript')[
				'waitForCompletion("%s", "%s", %d);' % (element_id, self.callback_url, self.interval)
			]
		else:
			content += tags.script(type='text/javascript')[
				'setProgress("%s", %d, %d);' % (element_id, self.value, self.maxvalue)
			]
		
		return content
