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
	
	def get_element(self, req, style, storable):
		frm = form.FormNode(self.name)
		frm(type='label', value=getattr(storable, self.name, ''))
		return frm
	
	def get_search_value(self, value):
		if(self.get('fulltext_search')):
			return persist.RAW(persist.interp("MATCH(%%s) AGAINST (%s)", [value]))
		else:
			return persist.RAW(persist.interp("INSTR(%%s, %s)", [value]))


class DateField(define.definition):
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		frm = form.FormNode(self.name)
		frm(type='label', value=getattr(storable, self.name, ''))
		return frm


class StringField(define.definition):
	implements(IDatatype)
	
	inherited_attributes = ['size', 'maxlength']
	
	def get_element(self, req, style, storable):
		frm = form.FormNode(self.name)
		frm(value=getattr(storable, self.name, ''))
		if(style == 'listing' or self.get('read_only', False)):
			frm(type='label')
		else:
			frm(type='textfield')
		return frm
	
	def get_search_value(self, value):
		if(self.get('fulltext_search')):
			return persist.RAW(persist.interp("MATCH(%%s) AGAINST (%s)", [value]))
		else:
			return persist.RAW(persist.interp("INSTR(%%s, %s)", [value]))


class TextAreaField(define.definition):
	implements(IDatatype)
	
	inherited_attributes = ['rows', 'cols']
	
	def get_element(self, req, style, storable):
		frm = form.FormNode(self.name)
		frm(value=getattr(storable, self.name, ''))
		if(style == 'listing' or self.get('read_only', False)):
			frm(type='label')
		else:
			frm(type='textarea')
		return frm
	
	def get_search_value(self, value):
		if(self.get('fulltext_search')):
			return persist.RAW(persist.interp("MATCH(%%s) AGAINST (%s)", [value]))
		else:
			return persist.RAW(persist.interp("INSTR(%%s, %s)", [value]))


class PasswordField(define.definition):
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		entry_frm = form.FormNode(self.name)
		entry_frm(value=getattr(storable, self.name, ''))
		
		if(style == 'listing' or self.get('read_only', False)):
			entry_frm(type='label')
			if(self.get('obfuscate', True)):
				entry_frm(value='********')
			return frm
		
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
			frm['entry'] = entry_frm
			frm['verify'] = verify_frm
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
			if(form_data[self.name]['entry'].value != form_data[self.name]['verify'].value):
				form.set_error(self.name, 'Sorry, those passwords do not match.')
				#print "%s doesn't match %s" % (form_data[entry_name], form_data[verify_name])
				return False
			
			# If there's nothing in both fields, return False
			if((not getattr(form_data[self.name]['entry'], 'value', '')) and (not getattr(form_data[self.name]['verify'], 'value', ''))):
				#print "no passwords in %s" % form_data
				# Remember, True means "I'm done with it", not "I wrote it"
				return True
			
			value = form_data[self.name]['entry'].value
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
