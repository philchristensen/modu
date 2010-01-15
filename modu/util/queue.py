# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Classes that manage a queue of items, optionally saving them in the session.

This is used for error reporting and storing of asynchronous content, such as
the current set of stylesheets or javascripts.
"""

def activate_messages(req):
	"""
	Messages are stored in the user's session, and displayed at appropriate times.
	"""
	req['modu.messages'] = Queue(req)

def activate_content_queue(req):
	"""
	Queue stylesheets or javascript for display by a content queue-aware template.
	"""
	req['modu.content'] = Queue(req, use_session=False, nodupes=True)

class Queue(object):
	"""
	A queue of items.
	"""
	def __init__(self, req, use_session=True, nodupes=False):
		"""
		Create a new queue.
		"""
		self.req = req
		self.use_session = use_session
		self.nodupes = nodupes
	
	def activate(self):
		"""
		Hook to deal with saving messages in the session.
		"""
		if(hasattr(self, 'messages')):
			return
		if('modu.session' in self.req and self.use_session):
			self.messages = self.req.session.setdefault('modu.messages', {})
		else:
			self.messages = {}
	
	def report(self, code, message):
		"""
		Add the item to an internal mini-queue.
		"""
		self.activate()
		if not(isinstance(message, (tuple, list))):
			message = [message]
		
		for m in message:
			queue = self.messages.setdefault(code, [])
			if(self.nodupes and m in queue):
				continue
			queue.append(m)
	
	def count(self, code):
		"""
		See how many items are contained in an internal mini-queue.
		"""
		self.activate()
		return len(self.messages.get(code, []))
	
	def get(self, code):
		"""
		Get all the items in an internal mini-queue.
		"""
		self.activate()
		if(code in self.messages):
			result = self.messages[code]
			if(self.use_session):
				del self.messages[code]
			return result
		return []