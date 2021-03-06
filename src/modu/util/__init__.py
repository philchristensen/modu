# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
Various utilities useful in building modu applications.
"""

class OrderedDict(dict):
	"""
	A dict subclass that preserves the order of entered keys.
	"""
	def __init__(self, data=None, **kwargs):
		"""
		Instantiate an OrderedDict.
		
		Examples::
			# Insert in order
			d = util.OrderedDict([('one', 1), ('two', 2), ('three', 3)])
			
			# Insert in order
			d = util.OrderedDict()
			d['one'] = 1
			d['two'] = 2
			d['three'] = 3
			
			# Insert randomly
			d = util.OrderedDict(one=1, two=2, three=3)
			
		"""
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
		"""
		Save the key order for serialization.
		"""
		return {'_order':self._order, '_data':self.dict()}
	
	def __setstate__(self, data):
		"""
		Restore the key order during unserialization.
		"""
		self._order = []
		for key in data.get('_order', []):
			self[key] = data['_data'][key]
	
	def __setitem__(self, key, value):
		"""
		Maintain key order.
		"""
		if not self.has_key(key):
			if not(hasattr(self, '_order')):
				self._order = []
			self._order.append(key)
		dict.__setitem__(self, key, value)
	
	def copy(self):
		"""
		Implement key-order-preserving copy.
		"""
		return self.__class__(self)
	
	def dict(self):
		"""
		Get a plain dict object for these items.
		"""
		plain = {}
		plain.update(self)
		return plain
	
	def __delitem__(self, key):
		"""
		Maintain key order.
		"""
		dict.__delitem__(self, key)
		self._order.remove(key)
	
	def iteritems(self):
		"""
		Maintain key order.
		"""
		for item in self._order:
			yield (item, self[item])
	
	def items(self):
		"""
		Maintain key order.
		"""
		return list(self.iteritems())
	
	def itervalues(self):
		"""
		Maintain key order.
		"""
		for item in self._order:
			yield self[item]
	
	def values(self):
		"""
		Maintain key order.
		"""
		return list(self.itervalues())
	
	def __iter__(self):
		return self.iterkeys()
	
	def iterkeys(self):
		"""
		Maintain key order.
		"""
		return iter(self._order)
	
	def keys(self):
		"""
		Maintain key order.
		"""
		return list(self._order)
	
	def popitem(self):
		"""
		Maintain key order.
		"""
		key = self._order[-1]
		value = self[key]
		del self[key]
		return (key, value)
	
	def setdefault(self, item, default):
		"""
		Maintain key order.
		"""
		if self.has_key(item):
			return self[item]
		self[item] = default
		return default
	
	def update(self, d):
		"""
		Maintain key order.
		"""
		for k, v in d.items():
			self[k] = v


