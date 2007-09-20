# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Various utilities useful in building modu applications.
"""

class OrderedDict(dict):
	def __init__(self, data=None, **kwargs):
		self._order = []
		if data is not None:
			if hasattr(data,'keys'):
				self.update(data)
			else:
				for k,v in data: # sequence
					self[k] = v
		if len(kwargs):
			self.update(kwargs)
	
	def __getstate__(self):
		return {'_order':self._order, '_data':self.dict()}
	
	def __setstate__(self, data):
		for key in data.get('_order', []):
			self[key] = data['_data'][key]
	
	def __setitem__(self, key, value):
		if not self.has_key(key):
			if not(hasattr(self, '_order')):
				self._order = []
			self._order.append(key)
		dict.__setitem__(self, key, value)
	
	def copy(self):
		return self.__class__(self)
	
	def dict(self):
		plain = {}
		plain.update(self)
		return plain
	
	def __delitem__(self, key):
		dict.__delitem__(self, key)
		self._order.remove(key)
	
	def iteritems(self):
		for item in self._order:
			yield (item, self[item])
	
	def items(self):
		return list(self.iteritems())
	
	def itervalues(self):
		for item in self._order:
			yield self[item]
	
	def values(self):
		return list(self.itervalues())
	
	def iterkeys(self):
		return iter(self._order)
	
	def keys(self):
		return list(self._order)
	
	def popitem(self):
		key = self._order[-1]
		value = self[key]
		del self[key]
		return (key, value)
	
	def setdefault(self, item, default):
		if self.has_key(item):
			return self[item]
		self[item] = default
		return default
	
	def update(self, d):
		for k, v in d.items():
			self[k] = v


