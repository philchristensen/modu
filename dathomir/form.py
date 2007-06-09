# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

class Form(object):
	def __init__(self, name):
		self.name = name
		self.fields = {}
	
	def __setitem__(self, key, value):
		if not(isinstance(value, (dict, Field))):
			raise ValueError('Form fields must be dictionaries or dathomir.form.Field instances.')
		
		if(isinstance(value, dict)):
			if(value['type'] == 'fieldset'):
				field = FieldSet(key, value)
			else:
				field = Field(key, value)
		else:
			field = value
		
		self.fields[key] = field
	
	def __getitem__(self, key):
		return self.fields[key]

class Field(object):
	def __init__(self, name, attribs):
		self.name = name
		self.rendered = False
		for key, value in attribs.iteritems():
			self.__setitem__(key, value)
	
	def __setitem__(self, key, value):
		pass

class FieldSet(Field):
	def __setitem__(self, key, value):
		pass

"""
Should this really work this way? Maybe it would be better to follow the
Django approach, and allow subclasses of storable to define the fields they
provide.

OTOH, that doesn't allow us to use the same interface for general form creation,
which was one of the annoying things about the PHP predecessor to dathomir.

It's important to keep a distinction between a form with fields in it and a
single database column whose data is represented by several fields in the form,
such as the timestamp date field (which has select fields for month, day, year)
"""