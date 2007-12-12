# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes for managing stringlike data.
"""

import time, datetime

from zope.interface import implements

from modu.editable import IDatatype, define
from modu.util import form, tags, date
from modu import persist

DAY = 86400
MONTH = DAY * 31
YEAR = DAY * 365

class DateField(define.definition):
	"""
	Allow editing of date data via a multiple select interface or javascript popup calendar.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		value = getattr(storable, self.get_column_name(), None)
		if(isinstance(value, (int, long))):
			value = datetime.datetime.utcfromtimestamp(value)
		
		if(self.get('read_only', False) or style == 'listing'):
			if(value):
				output = date.strftime(value, self.get('format_string', '%B %d, %Y at %I:%M%p'))
			else:
				output = 'no date set'
			frm = form.FormNode(self.name)
			frm(type='label', value=output)
			return frm
		
		if(value is None):
			current_year = datetime.datetime.now().year
		else:
			current_year = value.year
		start_year = self.get('start_year', current_year - 2)
		end_year = self.get('end_year', current_year + 5)
		
		months, days, years = date.get_date_arrays(start_year, end_year)
		
		frm = form.FormNode(self.name)
		frm(type='fieldset', style='brief')
		
		frm['null'](type='checkbox', text="no value", weight=-1, suffix=tags.br(), 
			attributes=dict(onChange='enableDateField(this);'))
		
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/jquery/jquery-1.2.1.js"))[''])
		req.content.report('header', tags.script(type='text/javascript')["""
			function enableDateField(checkboxField){
				var formItem = $(checkboxField).parent().parent()
				if(checkboxField.checked){
					formItem.children(':enabled').attr('disabled', true)
				}
				else{
					formItem.children(':disabled').attr('disabled', false)
				}
			}
		"""])
		
		attribs = {}
		if(value is None):
			if(self.get('default_now', False)):
				value = datetime.datetime.now()
			else:
				frm['null'](checked=True)
				attribs['disabled'] = None
		
		frm['date'](type=self.get('style', 'datetime'), value=value, attributes=attribs, start_year=start_year, end_year=end_year)
		
		return frm
	
	def update_storable(self, req, form, storable):
		"""
		@see: L{modu.editable.define.definition.update_storable()}
		"""
		if(self.get('read_only')):
			return True
		
		data = form.data['%s-form' % storable.get_table()][self.name]
		
		if(data.get('null', 0)):
			setattr(storable, self.get_column_name(), None)
			return True
		
		value = getattr(storable, self.get_column_name(), None)
		if(value is None):
			current_year = datetime.datetime.now().year
		else:
			current_year = value.year
		
		start_year = self.get('start_year', current_year - 2)
		end_year = self.get('end_year', current_year + 5)
		
		value = date.get_dateselect_value(data['date'], self.get('style', 'datetime'), start_year, end_year)
		
		save_format = self.get('save_format', 'timestamp')
		if(save_format == 'timestamp'):
			setattr(storable, self.get_column_name(), date.convert_to_timestamp(value))
		else:
			setattr(storable, self.get_column_name(), value)
		
		return True


