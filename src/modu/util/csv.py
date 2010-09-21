# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
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

def generate_csv(rows, le='\n', print_headers=True):
	return list(generate_csv_gen(rows, le, print_headers))

def generate_csv_gen(rows, le='\n', print_headers=True):
	"""
	Generate comma-separated value output from a list of dicts.
	
	The keys of the dict will be used as column headings, and
	are assumed to be identical for all rows.
	"""
	header_string = None if print_headers else ''
	
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
			yield header_string
		
		yield ','.join(fields) + le;

def generate_tsv(rows, le='\n'):
	return list(generate_tsv_gen(rows, le))

def generate_tsv_gen(rows, le='\n'):
	"""
	Generate tab-separated value output from a list of dicts.
	
	The keys of the dict will be used as column headings, and
	are assumed to be identical for all rows.
	"""
	header_string = None
	
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
			yield header_string
		yield '\t'.join(fields) + le;

def parse_line(line, column_names=None, separator=",", qualifier='"'):
	io = StringIO.StringIO(line)
	result = parse(io, column_names=column_names, separator=separator, qualifier=qualifier)
	return result[0]

def parse(stream, column_names=None, separator=",", qualifier='"'):
	return list(parse_gen(stream, column_names, separator, qualifier))

def parse_gen(stream, column_names=None, separator=",", qualifier='"'):
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
				# if we're not at the beginning, keep the qualifier
				# in the output. this allows use of OpenOffice TSV,
				# which has double quotes around field content, as well
				# as standard TSV with tabs but no quotes.
				if(len(buff)):
					buff += c
				qualified = True
		elif(c == separator):
			if(qualified):
				buff += c
			else:
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
					yield fields
				
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
		yield fields
	
	return
