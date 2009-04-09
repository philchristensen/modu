# modu
# Copyright (C) 2007-2008 Phil Christensen
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
from modu.persist import sql
from modu import persist, assets

DAY = 86400
MONTH = DAY * 31
YEAR = DAY * 365

class CurrentDateField(define.definition):
	"""
	Display a checkbox that allows updating a date field with the current date.
	"""
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		value = getattr(storable, self.get_column_name(), None)
		if(value):
			output = date.strftime(value, self.get('format_string', '%B %d, %Y at %I:%M%p'))
		else:
			output = ''
		
		if(style == 'search'):
			frm = form.FormNode(self.name)
			return frm
		elif(style == 'listing'):
			frm = form.FormNode(self.name)
			if(self.get('date_in_listing', True)):
				if(output == ''):
					output = '(none)'
				frm(type='label', value=output)
			else:
				frm(type='checkbox', disabled=True, checked=bool(output))
			return frm
		elif(style == 'detail' and self.get('read_only', False)):
			if(output == ''):
				output = '(none)'
			frm = form.FormNode(self.name)
			frm(type='label', value=output)
			return frm
		
		checked = bool(output)
		if(storable.get_id() == 0 and self.get('default_checked', False)):
			checked = True
		
		frm = form.FormNode(self.name)(
			type	= 'checkbox',
			checked	= checked,
			suffix	= '&nbsp;&nbsp;' + tags.small()[output],
		)
		
		if(bool(output)):
			frm(
				attributes = dict(
					disabled	= True,
				),
				suffix = tags.input(
					type	= 'hidden',
					name	= '%s-form[%s]' % (self.itemdef.name, self.name),
					value	= 1,
				) + frm.suffix
			)
		else:
			frm(
				text	= '&nbsp;&nbsp;' + tags.small(_class='minor-help')['check to set current date']
			)
		
		return frm
	
	def update_storable(self, req, form, storable):
		if(form[self.name].attr('checked', False)):
			value = datetime.datetime.now()
			save_format = self.get('save_format', 'timestamp')
			if(save_format == 'timestamp'):
				setattr(storable, self.get_column_name(), date.convert_to_timestamp(value))
			else:
				setattr(storable, self.get_column_name(), value)
		
		return True

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
		if(isinstance(value, (int, long, float))):
			value = datetime.datetime.utcfromtimestamp(value)
		
		if(style == 'search'):
			frm = form.FormNode(self.name)
			frm['from'] = self.get_form_element(req, '_detail', storable)(
				prefix='<div>from date:',
				suffix=tags.br() + '</div>',
			)
			frm['to'] = self.get_form_element(req, '_detail', storable)(
				prefix='<div>to date:',
				suffix='</div>',
			)
			return frm
		elif(style == 'listing' or (style == 'detail' and self.get('read_only', False))):
			if(value):
				output = date.strftime(value, self.get('format_string', '%B %d, %Y at %I:%M%p'))
			else:
				output = ''
			frm = form.FormNode(self.name)
			frm(type='label', value=output)
			return frm
		
		current_year = datetime.datetime.now().year
		if(value is not None):
			current_year = getattr(value, 'year', current_year)
		
		start_year = self.get('start_year', current_year - 2)
		end_year = self.get('end_year', current_year + 5)
		
		months, days, years = date.get_date_arrays(start_year, end_year)
		
		frm = form.FormNode(self.name)
		frm(type='fieldset', style='brief')
		
		frm['null'](type='checkbox', text="no value", weight=-1, suffix=tags.br(), 
			attributes=dict(onChange='enableDateField(this);'))
		
		req.content.report('header', tags.script(type="text/javascript",
			src=assets.get_jquery_path(req))[''])
		req.content.report('header', tags.script(type='text/javascript')["""
			function enableDateField(checkboxField){
				var formItem = $(checkboxField).parent().parent();
				if($(checkboxField).attr('checked')){
					formItem.children(':enabled').attr('disabled', true);
				}
				else{
					formItem.children(':disabled').attr('disabled', false);
				}
			}
		"""])
		
		attribs = {}
		
		if(value is None):
			frm['null'](checked=True)
			#attribs['disabled'] = None
			
			if(self.get('default_now', False)):
				value = datetime.datetime.now()
		
		frm['date'](
			type		= self.get('style', 'datetime'),
			value		= value,
			attributes	= attribs,
			start_year	= start_year,
			end_year	= end_year,
			suffix		= tags.script(type="text/javascript")["""
				enableDateField($('#form-item-%s input'));
			""" % self.name],
		)
		
		return frm
	
	def update_storable(self, req, form, storable):
		"""
		@see: L{modu.editable.define.definition.update_storable()}
		"""
		save_format = self.get('save_format', 'timestamp')
		
		if(self.get('read_only')):
			if(self.get('default_now', False) and not storable.get_id()):
				if(save_format == 'timestamp'):
					setattr(storable, self.get_column_name(), int(time.time()))
				else:
					setattr(storable, self.get_column_name(), datetime.datetime.now())
			return True
		
		data = form[self.name]['date']
		
		if(data.attr('null', 0)):
			setattr(storable, self.get_column_name(), None)
			return True
			
		start_year = data.start_year
		end_year = data.end_year
		
		date_data = req.data[form.name][self.name].get('date', None)
		if(date_data):
			value = date.get_dateselect_value(date_data, self.get('style', 'datetime'), start_year, end_year)
		else:
			value = None
		
		if(save_format == 'timestamp'):
			setattr(storable, self.get_column_name(), date.convert_to_timestamp(value))
		else:
			setattr(storable, self.get_column_name(), value)
		
		return True
	
	def get_search_value(self, value, req, frm):
		form_data = frm[self.name]
		
		to_value = 0
		from_value = 0
		
		if not(value['to'].get('null')):
			start_year = form_data['to']['date'].start_year
			end_year = form_data['to']['date'].end_year
			date_data = value['to'].get('date', None)
			if(date_data):
				to_value = date.get_dateselect_value(date_data, self.get('style', 'datetime'), start_year, end_year)
				to_value = time.mktime(to_value.timetuple())
		
		if not(value['from'].get('null')):
			start_year = form_data['from']['date'].start_year
			end_year = form_data['from']['date'].end_year
			date_data = value['from'].get('date', None)
			if(date_data):
				from_value = date.get_dateselect_value(date_data, self.get('style', 'datetime'), start_year, end_year)
				from_value = time.mktime(from_value.timetuple())
		
		if(to_value and from_value):
			if(self.get('save_format', 'timestamp') == 'datetime'):
				return sql.RAW('UNIX_TIMESTAMP(%%s) BETWEEN %s AND %s' % (from_value, to_value))
			else:
				return sql.RAW('%%s BETWEEN %s AND %s' % (from_value, to_value))
		elif(to_value):
			return sql.LT(to_value)
		elif(from_value):
			return sql.GT(from_value)
		else:
			return None


