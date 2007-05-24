# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

class URLNode(object):
	def __init__(self, leaf_data=None):
		self.children = {}
		self.leaf_data = None
		self.parsed_data = []
		self.parsed_path = []
		self.unparsed_path = []
		self.leaf_data = leaf_data
	
	def register(self, fragment, data):
		if(fragment == '/'):
			self.leaf_data = data
			return
		
		parts = filter(None, fragment.split('/'))
		
		node = self
		for i in range(len(parts)):
			segment = parts[i]
			#print 'node.children: ' + str(node.children)
			if(segment in node.children):
				if(i < len(parts)):
					#print 'inspecting child: ' + segment
					node = node.children[segment]
					if(i == len(parts) - 1):
						node.leaf_data = data
				else:
					raise ValueError("There is already a leaf node at %s" % fragment)
			else:
				if(i < len(parts)):
					#print 'creating child at: ' + segment
					node.children[segment] = URLNode()
					node = node.children[segment]
					if(i == len(parts) - 1):
						#print '1-setting leaf data to: ' + str(data)
						node.leaf_data = data
				else:
					#print '2-setting leaf data to: ' + str(data)
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
