# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
In an attempt to mimic the Drupal form-building process in a slightly more
Pythonic way, these classes will allow you to populate a Form object using
dictionary syntax.

Note that this will simply create a form definition. Separate classes/modules
will need to be used to render the form.
"""

class FormNode(object):
	def __init__(self, name):
		self.name = name
		self.rendered = False
		self.parent = None
		self.children = {}
		self.attributes = {}
		
		self.submit = None
		self.theme = None
		self.validate = None
	
	def __call__(self, *args, **kwargs):
		if('clobber' in kwargs and kwargs['clobber']):
			del kwargs['clobber']
			self.attributes = kwargs
			return
		
		for key, value in kwargs.iteritems():
			if(key in ('theme', 'validate', 'submit')):
				if not(callable(value)):
					raise TypeError("'%s' must be a callable object" % key)
				setattr(self, key, value)
			else:
				self.attributes[key] = value
	
	def __getitem__(self, key):
		if(key not in self.children):
			if(self.parent is not None and self.attributes['type'] == 'fieldset'):
				raise TypeError('Only forms and fieldsets can have child fields.')
			self.children[key] = FormNode(key)
			self.children[key].parent = self
		return self.children[key]

from mod_python import util

import re

NESTED_NAME = re.compile(r'([^\[]+)(\[([^\]]+)\])*')
KEYED_FRAGMENT = re.compile(r'\[([^\]]+)\]*')

class NestedFieldStorage(util.FieldStorage):
	def __init__(self, *args, **kwargs):
		super(self, NestedFieldStorage).__init__(*args, **kwargs)
		self.__nested_table_cache = {}
	
	def add_field(self, key, value):
		original_key = key
		tree = self._parse_name(key)
		if(len(tree) > 1):
			key = tree[0]
			node = self.__nested_table_cache
			# iterate through the key list
			while(tree):
				fragment = tree.pop()
				if(fragment in node):
					# Some kind of collision, just keep the
					# original key
					if not(isinstance(node[fragment], dict)):
						item = StringField(value)
						item.name = original_key
						self.list.append(item)
						break
					
				else:
					pass
		else:
			item = StringField(value)
			item.name = key
			self.list.append(item)
	
	def _parse_name(self, name):
		match = NESTED_NAME.match(name)
		tree = []
		if(match is not None):
			tree.append(match.group(1))
			tree.extend(KEYED_FRAGMENT.findall(name))
		return tree
