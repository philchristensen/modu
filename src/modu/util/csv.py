# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains ASCII import/export functions.
"""

try:
	import cStringIO as StringIO
except ImportError, e:
	import StringIO

from modu import util

def generate_csv(rows, le='\n'):
	"""
	Generate comma-separated value output from a list of dicts.
	
	The keys of the dict will be used as column headings, and
	are assumed to be identical for all rows.
	"""
	header_string = None
	content_string = ''
	
	for row in rows:
		headers = []
		fields = []
		
		for header, value in row.items():
			if(header_string is None):
				if(header.find('"') != -1 or header.find(',') != -1):
					headers.append('"%s"' % header.replace("\"","\"\""))
				else:
					headers.append(header)
			
			# make sure to escape quotes in the output
			# in MS Excel double-quotes are escaped with double-quotes so that's what we do here
			if(not isinstance(value, basestring)):
				value = str(value)
			if(value.find('"') != -1 or value.find(',') != -1):
				fields.append('"%s"' % value.replace("\"","\"\""))
			else:
				fields.append(value)
		
		if(header_string is None):
			header_string = ','.join(headers) + le;
		
		content_string += ','.join(fields) + le;
	
	if(header_string is None):
		header_string = ''
	
	return header_string + content_string

def generate_tsv(rows, le='\n'):
	"""
	Generate tab-separated value output from a list of dicts.
	
	The keys of the dict will be used as column headings, and
	are assumed to be identical for all rows.
	"""
	header_string = None
	content_string = ''
	
	for row in rows:
		headers = []
		fields = []
		
		for header, value in row.items():
			if(header_string is None):
				headers.append(header)
			
			if(not isinstance(value, basestring)):
				value = str(value)
			fields.append(value)
		
		if(header_string is None):
			header_string = '\t'.join(headers) + le;
		content_string += '\t'.join(fields) + le;
	
	if(header_string is None):
		header_string = ''
	
	return header_string + content_string

def parse_line(line, column_names=None, separator=",", qualifier='"'):
	io = StringIO.StringIO(line)
	result = parse(io, column_names=column_names, separator=separator, qualifier=qualifier)
	return result[0]

def parse(stream, column_names=None, separator=",", qualifier='"'):
	rows = []
	fields = []
	buff = ''
	qualified = False
	line_endings = ('\n', '\r')
	
	c = stream.read(1)
	while(c != ''):
		if(c == qualifier):
			if(qualified):
				buff += c
				c = stream.read(1)
				if(c != qualifier):
					qualified = False
					continue
			else:
				qualified = True
		elif(c == separator):
			if(qualified):
				buff += c
			else:
				qualified = False
				if(buff and buff[-1] == qualifier):
					buff = buff[0:-1]
				fields.append(buff)
				buff = ''
		elif(c in line_endings):
			if(qualified):
				buff += c
			else:
				old_c = c
				c = stream.read(1)
				if(buff):
					if(buff[-1] == qualifier):
						buff = buff[0:-1]
					fields.append(buff)
				if(column_names):
					fields = util.OrderedDict(zip(column_names, fields))
				if(fields):
					rows.append(fields)
				
				qualified = False
				fields = []
				buff = ''
				
				if(c == old_c or c not in line_endings):
					continue
		else:
			buff += c
		
		c = stream.read(1)
	
	if(buff):
		if(buff[-1] == qualifier):
			buff = buff[0:-1]
		fields.append(buff)
	if(column_names):
		fields = util.OrderedDict(zip(column_names, fields))
	if(fields):
		rows.append(fields)
	fields = []
	buff = ''
	
	return rows
