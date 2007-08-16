# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes for managing stringlike data.
"""

from twisted import plugin

from zope.interface import classProvides

from modu.web.editable import IDatatype, Field
from modu.util import form
from modu import persist

class LabelField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='label', value=getattr(storable, name, None))
		return frm


class DateField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='label', value=getattr(storable, name, None))
		return frm


class StringField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	inherited_attributes = ['size', 'maxlength']
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(value=getattr(storable, name, None))
		if(style == 'list'):
			frm(type='label')
		else:
			frm(type='textfield')
		return frm


class TextAreaField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	inherited_attributes = ['rows', 'cols']
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='textarea', value=getattr(storable, name, None))
		return frm


class PasswordField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		entry_frm = form.FormNode(name)
		entry_frm(value=getattr(storable, name, None))
		
		if(definition.get('obfuscate', True)):
			entry_frm(type='password')
		else:
			entry_frm(type='textfield')
		
		if(definition.get('verify', True)):
			entry_frm.name += '-entry'
			entry_frm.attributes['value'] = ''
			verify_frm = form.FormNode('%s-verify' % name)
			if(definition.get('obfuscate', True)):
				verify_frm(type='password')
			else:
				verify_frm(type='textfield')
			
			frm = form.FormNode(name)(type='fieldset', style='brief')
			frm.children['entry'] = entry_frm
			frm.children['verify'] = verify_frm
		else:
			frm = entry_frm
		
		return frm
	
	def update_storable(self, name, req, form, definition, storable):
		form_name = '%s-form' % storable.get_table()
		
		# There should be either a fieldset or a field at the regular name
		if(form_name not in form.data):
			#print '%s or %s not found in %s' % (form_name, name, form.data)
			return False
		
		form_data = form.data[form_name]
		
		# if 'verify' is in the definition, we expect a fieldset
		if(definition.get('verify', True)):
			entry_name = '%s-entry' % name
			verify_name = '%s-verify' % name
			
			# If there's nothing in both fields, return False
			if((not getattr(form_data[entry_name], 'value', None)) and (not getattr(form_data[verify_name], 'value', None))):
				#print "no passwords in %s" % form_data
				# Remember, True means "I'm done with it", not "I wrote it"
				return True
			
			if(form_data[entry_name].value != form_data[verify_name].value):
				form.set_field_error(name, 'Sorry, those passwords do not match.')
				#print "%s doesn't match %s" % (form_data[entry_name], form_data[verify_name])
				return False
			
			value = form_data[entry_name].value
		else:
			if(name not in form_data):
				#print '%s not found in %s' % (name, form_data)
				return False
			else:
				value = form_data[name].value
		
		if(definition.get('encrypt', True)):
			setattr(storable, name, persist.RAW("ENCRYPT('%s')" % value))
		else:
			setattr(storable, name, value)
		
		return True
