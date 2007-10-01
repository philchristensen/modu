# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Various date-related utilities useful in building modu applications.
"""

import time, datetime

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

def get_dateselect_value(date_post_data, style, start_year, end_year):
	value = 0
	
	months, days, years = get_date_arrays(start_year, end_year)
	
	def _safe_int(i):
		if(i == ''):
			return 0
		return int(i)
	
	if(style in ('date', 'datetime')):
		month = months[_safe_int(date_post_data['month'].value)]
		day = days[_safe_int(date_post_data['day'].value)]
		year = years[_safe_int(date_post_data['year'].value)]
		value += time.mktime(time.strptime('%s:%d:%d' % (month, day, year), '%B:%d:%Y'))
	if(style in ('datetime', 'time')):
		hours, minutes = get_time_arrays()
		hour = hours[_safe_int(date_post_data['hour'].value)]
		minute = minutes[_safe_int(date_post_data['minute'].value)]
		value += time.mktime(time.strptime('%s:1:1970:%s:%s' % (months[0], hour, minute), '%B:%d:%Y:%H:%M'))
		value -= time.timezone
	
	return value
