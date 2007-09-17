# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def activate_messages(req):
	req['modu.messages'] = Queue(req)

def activate_content_queue(req):
	req['modu.content'] = Queue(req, False, True)

class Queue(object):
	def __init__(self, req, use_session=True, nodupes=False):
		self.req = req
		self.use_session = use_session
		self.nodupes = nodupes
	
	def activate(self):
		if(hasattr(self, 'messages')):
			return
		if('modu.session' in self.req and self.use_session):
			self.messages = self.req.session.setdefault('modu.messages', {})
		else:
			self.messages = {}
	
	def report(self, code, message):
		self.activate()
		if not(isinstance(message, (tuple, list))):
			message = [message]
		
		for m in message:
			queue = self.messages.setdefault(code, [])
			if(self.nodupes and m in queue):
				continue
			queue.append(m)
	
	def count(self, code):
		self.activate()
		return len(self.messages.get(code, []))
	
	def get(self, code):
		self.activate()
		if(code in self.messages):
			result = self.messages[code]
			del self.messages[code]
			return result
		return []