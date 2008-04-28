# modu
# Copyright (C) 2007-2008 Phil Christensen
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
from modu.persist import sql

class SearchFieldMixin(object):
	"""
	A convenient Mixin for text-based searching.
	"""
	def get_search_value(self, value):
		"""
		@see: L{modu.editable.define.definition.get_search_value()}
		"""
		if(value is ''):
			return None
		
		if(self.get('fulltext_search')):
			return sql.RAW(sql.interp("MATCH(%%s) AGAINST (%s)", [value]))
		elif(self.get('exact_match')):
			return value
		else:
			return sql.RAW(sql.interp("INSTR(%%s, %s)", [value]))


class LabelField(SearchFieldMixin, define.definition):
	"""
	Display this field's contents as a read-only value.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		frm = form.FormNode(self.name)
		if(style == 'search'):
			frm(type='textfield', size=10) 
		else:
			frm(type='label', value=getattr(storable, self.get_column_name(), ''))
		return frm


class StringField(SearchFieldMixin, define.definition):
	"""
	Allow editing of a string field value.
	"""
	implements(IDatatype)
	
	inherited_attributes = ['size', 'maxlength']
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		frm = form.FormNode(self.name)
		frm(value=getattr(storable, self.get_column_name(), ''))
		if(style == 'listing' or self.get('read_only', False)):
			frm(type='label')
		else:
			frm(type='textfield')
		return frm


class HiddenField(SearchFieldMixin, define.definition):
	"""
	Allow editing of a string field value.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		frm = form.FormNode(self.name)
		frm(value=getattr(storable, self.get_column_name(), ''))
		if(style == 'listing' or self.get('read_only', False)):
			frm(type='label')
		else:
			frm(type='hidden')
		return frm


class TextAreaField(SearchFieldMixin, define.definition):
	"""
	Allow editing of a string field value using a TextArea field.
	"""
	implements(IDatatype)
	
	inherited_attributes = ['rows', 'cols']
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		frm = form.FormNode(self.name)
		frm(value=getattr(storable, self.get_column_name(), ''))
		if(style == 'listing' or self.get('read_only', False)):
			frm(type='label')
		elif(style == 'search'):
			frm(type='textfield', size=20)
		else:
			frm(type='textarea')
		return frm


class PasswordField(define.definition):
	"""
	Allow editing of an optionally encrypted password field.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		entry_frm = form.FormNode(self.name)
		entry_frm(value=getattr(storable, self.get_column_name(), ''))
		
		if(style == 'listing' or self.get('read_only', False)):
			entry_frm(type='label')
			if(self.get('obfuscate', True)):
				entry_frm(value='********')
			return entry_frm
		elif(style == 'search'):
			entry_frm(type='textfield', size=20)
			return entry_frm
		
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
		"""
		@see: L{modu.editable.define.definition.update_storable()}
		"""
		form_name = '%s-form' % storable.get_table()
		
		# There should be either a fieldset or a field at the regular name
		if(form_name not in req.data):
			#print '%s or %s not found in %s' % (form_name, name, req.data)
			return False
		
		form_data = req.data[form_name]
		
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
			setattr(storable, self.get_column_name(), sql.RAW("ENCRYPT('%s')" % value))
		else:
			setattr(storable, self.get_column_name(), value)
		
		return True
