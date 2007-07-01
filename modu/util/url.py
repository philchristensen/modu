# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import re

URL_REGEXP = r'(?P<scheme>[+a-z]+)\:(\/\/)?'
URL_REGEXP += r'((?P<user>\w+?)(\:(?P<password>\w+?))?\@)?'
URL_REGEXP += r'(?P<host>[\._\-a-z0-9]+)(\:(?P<port>\d+))?'
URL_REGEXP += r'(?P<path>/[^\s;?#]*)(;(?P<params>[^\s?#]*))?'
URL_REGEXP += r'(\?(?P<query>[^\s#]*))?(\#(?P<fragment>[^\s]*))?'
URL_RE = re.compile(URL_REGEXP, re.IGNORECASE)

def urlparse(url):
	match = URL_RE.match(url)
	return match.groupdict()

class URLNode(object):
	def __init__(self, leaf_data=None):
		self.children = {}
		self.leaf_data = None
		self.parsed_data = []
		self.parsed_path = []
		self.unparsed_path = []
		self.leaf_data = leaf_data
	
	def __str__(self):
		content = "URLNode(%r)[" % self.leaf_data
		for key in self.children:
			content += "%s:%s, " % (key, str(self.children[key]))
		content += "]"
		return content
	
	def register(self, fragment, data):
		if(fragment == '/'):
			self.leaf_data = data
			return
		
		parts = filter(None, fragment.split('/'))
		
		node = self
		for i in range(len(parts)):
			segment = parts[i]
			if(segment in node.children):
				node = node.children[segment]
				if(i == len(parts) - 1):
					if(node.leaf_data is None):
						node.leaf_data = data
					else:
						raise ValueError("There is already a leaf node at %s" % fragment)
			else:
				node.children[segment] = URLNode()
				node = node.children[segment]
				if(i == len(parts) - 1):
					node.leaf_data = data
	
	def parse(self, fragment):
		self.unparsed_path = filter(None, fragment.split('/'))
		
		node = self
		while(self.unparsed_path):
			segment = self.unparsed_path.pop(0)
			if(segment not in node.children):
				self.unparsed_path.insert(0, segment)
				self.parsed_data = node.leaf_data
				return self.parsed_data
				
			self.parsed_path.append(segment)
			node = node.children[segment]
		
		self.parsed_data = node.leaf_data
		return self.parsed_data
	
	def has_path(self, fragment):
		unparsed_path = filter(None, fragment.split('/'))
		
		node = self
		while(unparsed_path):
			segment = unparsed_path.pop(0)
			if(segment not in node.children):
				return node.leaf_data is not None
			
			node = node.children[segment]
		
		return node.leaf_data is not None
