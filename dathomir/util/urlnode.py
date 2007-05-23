# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

class URLNode(object):
    tree = {}
    leaf_data = None
    parsed_data = []
    parsed_path = []
    unparsed_path = []
    
    def __init__(self, leaf_data=None):
        self.leaf_data = leaf_data
    
    def register(self, fragment, data):
        if(fragment == '/'):
            self.leaf_data = data
        
        parts = fragment.split('/')
        if not(parts[0]):
            parts.pop(0)
        
        node = self
        for i in range(len(parts)):
            segment = parts[i]
            if(segment in node.tree):
                if(i < len(parts) - 1):
                    existing_data = node.tree[segment]
                    if(isinstance(existing_data, URLNode)):
                        node = existing_data
                    else:
                        node = node.tree[segment] = URLNode(existing_data)
                else:
                    raise ValueError("There is already a leaf node at %s" % fragment)
            else:
                if(i < len(parts) - 1):
                    node.tree[segment] = URLNode()
                    node = node.tree[segment]
                else:
                    node.tree[segment] = data
    
    def parse(self, fragment):
        self.unparsed_path = fragment.split('/')
        if not(self.unparsed_path[0]):
            self.unparsed_path.pop(0)
        
        node = self
        data = self.leaf_data
        while(self.unparsed_path):
            segment = self.unparsed_path.pop(0)
            if(segment not in node.tree):
                self.unparsed_path.insert(0, segment)
                self.parsed_data = data
                return data
                
            self.parsed_path.append(segment)
            
            data = node.tree[segment]
            if not(isinstance(data, URLNode)):
                break
            
            node = data
        
        if(isinstance(data, URLNode)):
            self.parsed_data = data.leaf_data
            return data.leaf_data
        
        self.parsed_data = data
        return data
    
    def has_registered_path(self, fragment):
        unparsed_path = fragment.split('/')
        if not(unparsed_path[0]):
            unparsed_path.pop(0)
        
        node = self
        data = self.leaf_data
        while(unparsed_path):
            segment = unparsed_path.pop(0)
            if(segment in node.tree):
                return True
        
        return False