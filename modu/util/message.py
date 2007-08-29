# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def activate_queue(req):
	req['modu.messages'] = Queue(req)

class Queue(object):
	def __init__(self, req):
		self.req = req
	
	def activate(self):
		if(hasattr(self, 'messages')):
			return
		if('modu.session' in self.req):
			self.messages = self.req.session.setdefault('modu.messages', {})
		else:
			self.messages = {}
	
	def report(self, code, message):
		self.activate()
		if not(isinstance(message, (tuple, list))):
			message = [message]
		for m in message:
			self.messages.setdefault(code, []).append(m)
	
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