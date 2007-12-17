# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Various utilities useful in building modu applications.
"""

def generate_csv(rows, le='\n'):
	header_string = None
	content_string = ''
	
	for row in rows:
		headers = []
		fields = []
		
		for header, value in row.items():
			if(header_string is None):
				if(header.find('"') != -1 or header.find(',') != -1):
					headers.append('"%s"' % header.replace("\"","\"\""))
				else:
					headers.append(header)
			
			# make sure to escape quotes in the output
			# in MS Excel double-quotes are escaped with double-quotes so that's what we do here
			if(not isinstance(value, basestring)):
				value = str(value)
			if(value.find('"') != -1 or value.find(',') != -1):
				fields.append('"%s"' % value.replace("\"","\"\""))
			else:
				fields.append(value)
		
		if(header_string is None):
			header_string = ','.join(headers) + le;
		
		content_string += ','.join(fields) + le;
	
	if(header_string is None):
		header_string = ''
	
	return header_string + content_string

def generate_tsv(rows, le='\n'):
	header_string = None
	content_string = ''
	
	for row in rows:
		headers = []
		fields = []
		
		for header, value in row.items():
			if(header_string is None):
				headers.append(header)
			
			if(not isinstance(value, basestring)):
				value = str(value)
			fields.append(value)
		
		if(header_string is None):
			header_string = '\t'.join(headers) + le;
		content_string += '\t'.join(fields) + le;
	
	if(header_string is None):
		header_string = ''
	
	return header_string + content_string

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
		self._order = []
		for key in data.get('_order', []):
			# I don't think __setitem__ is called during
			# the run of this function, so we manage order
			# ourselves
			self._order.append(key)
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


