# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import re

NESTED_NAME = re.compile(r'([^\[]+)(\[([^\]]+)\])*')
KEYED_FRAGMENT = re.compile(r'\[([^\]]+)\]*')

class FormNode(object):
	"""
	In an attempt to mimic the Drupal form-building process in a slightly more
	Pythonic way, this class allows you to populate a Form object using
	dictionary-like syntax.
	
	Note that this will simply create a form definition. Separate classes/modules
	will need to be used to render the form.
	"""
	
	def __init__(self, name):
		self.name = name
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
			if(self.parent is not None and self.attributes['type'] != 'fieldset'):
				raise TypeError('Only forms and fieldsets can have child fields.')
			self.children[key] = FormNode(key)
			self.children[key].parent = self
		return self.children[key]

try:
	from mod_python import util
	
	class NestedFieldStorage(util.FieldStorage):
		"""
		NestedFieldStorage allows you to use a dict-like syntax for
		naming your form elements. This allows related values to be
		grouped together, and retrieved as a single dict.
	
		(who'd'a thunk it, stealing from PHP...)
		"""
		def __init__(self, req, *args, **kwargs):
			self.__nested_table_cache = {}
			self.req = req
			util.FieldStorage.__init__(self, req, *args, **kwargs)
	
		def add_field(self, key, value):
			original_key = key
			tree = self._parse_name(key)
			new = False
			if(len(tree) > 1):
				key = tree[0]
				node = self.__nested_table_cache
				# iterate through the key list
				try:
					while(tree):
						fragment = tree.pop(0)
						if(fragment in node):
							if(tree):
								if(isinstance(node[fragment], dict)):
									node = node[fragment]
								else:
									raise ValueError('bad naming scheme')
							else:
								raise ValueError('bad naming scheme')
						else:
							if(node == self.__nested_table_cache):
								self.req.log_error(fragment + ' is new')
								new = True
							if(tree):
								node[fragment] = {}
								node = node[fragment]
							else:
								node[fragment] = value
				except ValueError:
					# Some kind of collision, just keep the
					# original key
					item = util.StringField(value)
					item.name = original_key
					self.list.append(item)
				else:
					if(new):
						item = DictField(self.__nested_table_cache[key])
						item.name = key
						self.list.append(item)
			else:
				item = util.StringField(value)
				item.name = key
				self.list.append(item)
	
		def _parse_name(self, name):
			match = NESTED_NAME.match(name)
			tree = []
		
			if(match is not None):
				tree.append(match.group(1))
				matches = KEYED_FRAGMENT.findall(name)
				tree.extend(matches)
		
			return tree
	
	class DictField(dict):
		pass
except:
	pass