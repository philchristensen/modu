# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes for managing stringlike data.
"""

from zope.interface import implements

from modu.editable import IDatatype, define
from modu.util import form
from modu import persist

class LabelField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		frm = form.FormNode(self.name)
		frm(type='label', value=getattr(storable, self.name, None))
		return frm


class DateField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		frm = form.FormNode(self.name)
		frm(type='label', value=getattr(storable, self.name, None))
		return frm


class StringField(define.definition):
	implements(IDatatype)
	
	inherited_attributes = ['size', 'maxlength']
	
	def get_element(self, style, storable):
		frm = form.FormNode(self.name)
		frm(value=getattr(storable, self.name, None))
		if(style == 'list'):
			frm(type='label')
		else:
			frm(type='textfield')
		return frm


class TextAreaField(define.definition):
	implements(IDatatype)
	
	inherited_attributes = ['rows', 'cols']
	
	def get_element(self, style, storable):
		frm = form.FormNode(self.name)
		frm(type='textarea', value=getattr(storable, self.name, None))
		return frm


class PasswordField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		entry_frm = form.FormNode(self.name)
		entry_frm(value=getattr(storable, self.name, None))
		
		if(self.get('obfuscate', True)):
			entry_frm(type='password')
		else:
			entry_frm(type='textfield')
		
		if(self.get('verify', True)):
			entry_frm.name += '-entry'
			entry_frm.attributes['value'] = ''
			verify_frm = form.FormNode('%s-verify' % self.name)
			if(self.get('obfuscate', True)):
				verify_frm(type='password')
			else:
				verify_frm(type='textfield')
			
			frm = form.FormNode(self.name)(type='fieldset', style='brief')
			frm.children['entry'] = entry_frm
			frm.children['verify'] = verify_frm
		else:
			frm = entry_frm
		
		return frm
	
	def update_storable(self, req, form, storable):
		form_name = '%s-form' % storable.get_table()
		
		# There should be either a fieldset or a field at the regular name
		if(form_name not in form.data):
			#print '%s or %s not found in %s' % (form_name, name, form.data)
			return False
		
		form_data = form.data[form_name]
		
		# if 'verify' is in the definition, we expect a fieldset
		if(self.get('verify', True)):
			entry_name = '%s-entry' % self.name
			verify_name = '%s-verify' % self.name
			
			if(form_data[entry_name].value != form_data[verify_name].value):
				form.set_error(self.name, 'Sorry, those passwords do not match.')
				#print "%s doesn't match %s" % (form_data[entry_name], form_data[verify_name])
				return False
			
			# If there's nothing in both fields, return False
			if((not getattr(form_data[entry_name], 'value', None)) and (not getattr(form_data[verify_name], 'value', None))):
				#print "no passwords in %s" % form_data
				# Remember, True means "I'm done with it", not "I wrote it"
				return True
			
			value = form_data[entry_name].value
		else:
			if(self.name not in form_data):
				#print '%s not found in %s' % (name, form_data)
				return False
			else:
				value = form_data[self.name].value
		
		if(self.get('encrypt', True)):
			setattr(storable, self.name, persist.RAW("ENCRYPT('%s')" % value))
		else:
			setattr(storable, self.name, value)
		
		return True
