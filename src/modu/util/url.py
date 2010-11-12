# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

import re

URL_REGEXP = r'(?P<scheme>[+a-z0-9]+)\:(\/\/)?'
URL_REGEXP += r'((?P<user>\w+?)(\:(?P<passwd>\w+?))?\@)?'
URL_REGEXP += r'(?P<host>[\._\-a-z0-9]+)(\:(?P<port>\d+))?'
URL_REGEXP += r'(?P<path>/[^\s;?#]*)(;(?P<params>[^\s?#]*))?'
URL_REGEXP += r'(\?(?P<query>[^\s#]*))?(\#(?P<fragment>[^\s]*))?'
URL_RE = re.compile(URL_REGEXP, re.IGNORECASE)

def urlparse(url):
	match = URL_RE.match(url)
	if not(match):
		return {}
	return match.groupdict()

class URLNode(object):
	def __init__(self, leaf_data=None):
		self.children = {}
		self.parsed_data = []
		self.prepath = []
		self.postpath = []
		self.leaf_data = leaf_data
	
	def __str__(self):
		content = "URLNode(%r)[" % (self.leaf_data,)
		for key in self.children:
			content += "%s:%s, " % (key, str(self.children[key]))
		content += "]"
		return content
	
	def register(self, fragment, data, clobber=False):
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
					if(node.leaf_data is None or clobber):
						node.leaf_data = data
					else:
						raise ValueError("There is already a leaf node at %s" % fragment)
			else:
				node.children[segment] = URLNode()
				node = node.children[segment]
				if(i == len(parts) - 1):
					node.leaf_data = data
	
	def parse(self, fragment):
		prepath = []
		postpath = filter(None, fragment.split('/'))
		
		node = self
		while(postpath):
			segment = postpath.pop(0)
			if(segment not in node.children):
				postpath.insert(0, segment)
				return node.leaf_data, prepath, postpath
				
			prepath.append(segment)
			node = node.children[segment]
		
		return node.leaf_data, prepath, postpath
	
	def get_data_at(self, fragment):
		postpath = filter(None, fragment.split('/'))
		
		node = self
		while(postpath):
			segment = postpath.pop(0)
			if(segment not in node.children):
				return node.leaf_data
			
			node = node.children[segment]
		
		return node.leaf_data
	
	def has_path(self, fragment):
		return self.get_data_at(fragment) is not None
