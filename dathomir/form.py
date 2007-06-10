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

from dathomir.util import form

class FormDef(object):
	def __init__(self, name):
		self.name = name
		self.rendered = False
		self.children = {}
		self.attributes = {}
		self.submit_hook = None
		self.validate_hook = None
	
	def __call__(self, *args, **kwargs):
		for key, value in kwargs.iteritems():
			self.attributes[key] = value
	
	def __getitem__(self, key, value):
		if(key not in children):
			self.children[key] = FormDef(key)
		return self.children[key]
