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
from modu.util import form, tags
from modu import persist

DAY = 86400
MONTH = DAY * 31
YEAR = DAY * 365

def get_date_arrays(start_year, end_year):
	def _get_month_struct(t):
		st = list(time.localtime())
		st[1] = t
		return st
	months = [time.strftime('%B', _get_month_struct(t)) for t in range(1, 13)]
	years = range(start_year, end_year + 1)
	days = range(1, 32)
	return months, days, years


def get_time_arrays():
	hours = [str(i).zfill(2) for i in range(25)]
	minutes = [str(i).zfill(2) for i in range(60)]
	return hours, minutes


def convert_to_timestamp(value):
	if(isinstance(value, (datetime.datetime, datetime.date))):
		return time.mktime(value.timetuple())
	else:
		return value

class DateField(define.definition):
	"""
	Allow editing of date data via a multiple select interface or javascript popup calendar.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		current_year = int(time.strftime('%Y', time.localtime()))
		start_year = self.get('start_year', current_year - 2)
		end_year = self.get('end_year', current_year + 5)
		
		months, days, years = get_date_arrays(start_year, end_year)
		
		frm = form.FormNode(self.name)
		frm(type='fieldset', style='brief')
		
		frm['null'](type='checkbox', text="no value", weight=-1, suffix=tags.br(), 
			attributes=dict(onChange='enableDateField(this);'))
		
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
		
		value = convert_to_timestamp(getattr(storable, self.get_column_name(), None))
		
		attribs = {}
		if(value is None):
			frm['null'](checked=True)
			attribs['disabled'] = None
			month, day, year, hour, minute = (months[0], 1, years[0], '00', '00')
		else:
			month, day, year, hour, minute = time.strftime('%B:%d:%Y:%H:%M', time.localtime(value)).split(':')
		
		if(self.get('style', 'datetime') in ('date', 'datetime')):
			frm['month'](type='select', weight=0, options=months, value=months.index(month), attributes=attribs)
			frm['day'](type='select', weight=1, options=days, value=days.index(int(day)), attributes=attribs)
			frm['year'](type='select', weight=2, options=years, value=years.index(int(year)), attributes=attribs)
		if(self.get('style', 'datetime') in ('datetime', 'time')):
			hours, minutes = get_time_arrays()
			frm['hour'](type='select', weight=3, options=hours, value=hours.index(hour), attributes=attribs)
			frm['minute'](type='select', weight=4, options=minutes, value=minutes.index(minute), attributes=attribs)
		
		return frm
	
	def update_storable(self, req, form, storable):
		"""
		@see: L{modu.editable.define.definition.update_storable()}
		"""
		data = form.data['%s-form' % storable.get_table()][self.name]
		
		if(data.get('null', 0)):
			setattr(storable, self.get_column_name(), None)
			return True
		
		value = 0
		
		current_year = int(time.strftime('%Y', time.localtime()))
		start_year = self.get('start_year', current_year - 2)
		end_year = self.get('end_year', current_year + 5)
		
		months, days, years = get_date_arrays(start_year, end_year)
		
		def _safe_int(i):
			if(i == ''):
				return 0
			return int(i)
		
		if(self.get('style', 'datetime') in ('date', 'datetime')):
			month = months[_safe_int(data['month'].value)]
			day = days[_safe_int(data['day'].value)]
			year = years[_safe_int(data['year'].value)]
			value += time.mktime(time.strptime('%s:%d:%d' % (month, day, year), '%B:%d:%Y'))
		if(self.get('style', 'datetime') in ('datetime', 'time')):
			hours, minutes = get_time_arrays()
			hour = hours[_safe_int(data['hour'].value)]
			minute = minutes[_safe_int(data['minute'].value)]
			value += time.mktime(time.strptime('%s:1:1970:%s:%s' % (months[0], hour, minute), '%B:%d:%Y:%H:%M'))
			value -= time.timezone
		
		save_format = self.get('save_format', 'timestamp')
		if(save_format == 'date'):
			setattr(storable, self.get_column_name(), datetime.date.fromtimestamp(value))
		elif(save_format == 'datetime'):
			setattr(storable, self.get_column_name(), datetime.datetime.fromtimestamp(value))
		elif(save_format == 'time'):
			setattr(storable, self.get_column_name(), datetime.timedelta(seconds=value))
		else:
			setattr(storable, self.get_column_name(), value)
		
		return True


