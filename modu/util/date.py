# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Various date-related utilities useful in building modu applications.
"""

import time, datetime

def strftime(dt, fmt):
	"""
	Format the provided datetime object using the given format string.
	
	This function will properly format dates before 1900.
	"""
	# I hope I did this math right. Every 28 years the
	# calendar repeats, except through century leap years
	# excepting the 400 year leap years.  But only if
	# you're using the Gregorian calendar.
	
	# Created by Andrew Dalke
	# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/306860
	
	if(dt == None):
		return ''
	
	# WARNING: known bug with "%s", which is the number
	# of seconds since the epoch.	This is too harsh
	# of a check.	It should allow "%%s".
	fmt = fmt.replace("%s", "s")
	if dt.year > 1900:
		return time.strftime(fmt, dt.timetuple())
	
	year = dt.year
	# For every non-leap year century, advance by
	# 6 years to get into the 28-year repeat cycle
	delta = 2000 - year
	off = 6*(delta // 100 + delta // 400)
	year = year + off
	
	def _findall(text, substr):
		"""
		matching support function.
		"""
		# Also finds overlaps
		sites = []
		i = 0
		while 1:
			j = text.find(substr, i)
			if j == -1:
				break
			sites.append(j)
			i=j+1
		return sites
	
	# Move to around the year 2000
	year = year + ((2000 - year)//28)*28
	timetuple = dt.timetuple()
	s1 = time.strftime(fmt, (year,) + timetuple[1:])
	sites1 = _findall(s1, str(year))
	
	s2 = time.strftime(fmt, (year+28,) + timetuple[1:])
	sites2 = _findall(s2, str(year+28))
	
	sites = []
	for site in sites1:
		if site in sites2:
			sites.append(site)
	
	s = s1
	syear = "%4d" % (dt.year,)
	for site in sites:
		s = s[:site] + syear + s[site+4:]
	return s

def format_seconds(seconds, colon_format=True):
	"""
	Format seconds as HH:MM:SS.
	"""
	if(seconds is None):
		return ''
	
	hours, remainder = divmod(int(seconds), 3600)
	minutes, remainder = divmod(remainder, 60)
	seconds = remainder
	
	__found = False
	def __zeroes(num):
		if(num or __found):
			__found = True
			return num
	
	if(colon_format):
		# hic sunt dracones
		result = ':'.join(map(lambda(i): str(i).zfill(2), [hours, minutes, seconds])).lstrip('0:')
		# ...seriously, what was i thinking? that was so uneccessary...
		if(result and result.find(':') == -1):
			result = ':' + result
	else:
		result = ''
		if(hours):
			result += str(hours) + 'h'
		if(minutes):
			result += str(minutes) + 'm'
		if(seconds):
			result += str(seconds) + 's'
	return result


def get_date_arrays(start_year, end_year):
	"""
	Get a set of array for creating date select fields.
	"""
	def _get_month_struct(t):
		st = list(time.localtime())
		st[1] = t
		return st
	months = [time.strftime('%B', _get_month_struct(t)) for t in range(1, 13)]
	years = range(start_year, end_year + 1)
	days = range(1, 32)
	return months, days, years


def get_time_arrays():
	"""
	Get a set of array for creating time select fields.
	"""
	hours = [str(i).zfill(2) for i in range(25)]
	minutes = [str(i).zfill(2) for i in range(60)]
	return hours, minutes


def convert_to_timestamp(value):
	"""
	Convert dates and datetimes to seconds since the epoch.
	"""
	if(isinstance(value, (datetime.datetime, datetime.date))):
		return time.mktime(value.timetuple())
	else:
		return value

def get_dateselect_value(date_post_data, style, start_year, end_year):
	"""
	Take a standard date select posting and create a date, datetime, or time object.
	"""
	value = 0
	
	months, days, years = get_date_arrays(start_year, end_year)
	
	def _safe_int(i):
		if(i == ''):
			return 0
		return int(i)
	
	if(style in ('date', 'datetime')):
		month = int(date_post_data['month'].value) + 1
		day = days[_safe_int(date_post_data['day'].value)]
		year = years[_safe_int(date_post_data['year'].value)]
		#value += time.mktime(time.strptime('%s:%d:%d' % (month, day, year), '%B:%d:%Y'))
	if(style in ('datetime', 'time')):
		hours, minutes = get_time_arrays()
		hour = hours[_safe_int(date_post_data['hour'].value)]
		minute = minutes[_safe_int(date_post_data['minute'].value)]
		#value += time.mktime(time.strptime('%s:1:1970:%s:%s' % (months[0], hour, minute), '%B:%d:%Y:%H:%M'))
		#value -= time.timezone
	
	if(style == 'date'):
		value = datetime.date(year, month, day)
	elif(style == 'datetime'):
		value = datetime.datetime(year, month, day, int(hour), int(minute))
	elif(style == 'time'):
		value = datetime.time(int(hour), int(minute))
	
	return value
