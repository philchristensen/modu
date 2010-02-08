# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage boolean-type fields.
"""

from zope.interface import implements

from modu.persist import sql
from modu.editable import IDatatype, define
from modu.util import form
from modu import persist

class CheckboxField(define.definition):
	"""
	Displays a field as an HTML checkbox.
	
	Provides modified update behavior to deal with the fact that checkboxes
	only submit form data when checked.
	"""
	implements(IDatatype)
	search_list = ['unchecked', 'checked', 'no search']
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		frm = form.FormNode(self.name)
		if(style == 'search'):
			search_value = getattr(storable, self.get_column_name(), '2')
			frm(type='radiogroup', options=self.search_list, value=search_value)
		else:
			frm(type='checkbox', value=self.get('checked_value', 1))
			if(str(getattr(storable, self.get_column_name(), None)) == str(self.get('checked_value', 1))):
				frm(checked=True)
			
			default_value = self.get('default_value', None)
			if(not storable.get_id() and default_value is not None):
				frm(checked=bool(default_value))
			
			if(style == 'listing' or self.get('read_only', False)):
				frm(disabled=True)
		
		return frm
	
	def get_search_value(self, value, req, frm):
		if(value is not None):
			value = value.value
			if(value == '0'):
				return sql.RAW('IFNULL(%%s, 0) <> %s' % self.get('checked_value', 1))
			elif(value == '1'):
				return sql.RAW('IFNULL(%%s, 0) = %s' % self.get('checked_value', 1))
		# a trick
		return sql.RAW('COALESCE(%s, 1, 1)')
	
	def update_storable(self, req, form, storable):
		"""
		@see: L{modu.editable.define.definition.update_storable()}
		"""
		form_name = '%s-form' % storable.get_table()
		if(form_name in req.data):
			form_data = req.data[form_name]
			if(self.name in form_data):
				setattr(storable, self.get_column_name(), form_data[self.name].value)
			else:
				setattr(storable, self.get_column_name(), self.get('unchecked_value', 0))
		return True


class NonNullSearchField(define.definition):
	search_list = ['empty', 'not empty', 'no search']
	
	def get_element(self, req, style, storable):
		if(style != 'search'):
			return form.FormNode(self.name)(type='label', value='n/a - Search Use Only')
		else:
			search_value = getattr(storable, self.get_column_name(), '2')
			frm = form.FormNode(self.name)
			frm(type='radiogroup', options=self.search_list, value=search_value)
			return frm
	
	def get_search_value(self, value, req, frm):
		if(value is not None):
			if(value.value == '0'):
				return sql.RAW('ISNULL(%s)')
			elif(value.value == '1'):
				return sql.RAW('NOT(ISNULL(%s))')
		
		# a trick
		return sql.RAW('IF(%s, 1, 1)')
	
	def update_storable(self, req, form, storable):
		pass

class NonBlankSearchField(NonNullSearchField):
	def get_search_value(self, value, req, frm):
		if(value is not None):
			if(value.value == '0'):
				return sql.RAW('ISNULL(%s)')
			elif(value.value == '1'):
				return sql.RAW("IFNULL(%s, '') <> ''")
		
		# a trick
		return sql.RAW('IF(%s, 1, 1)')
