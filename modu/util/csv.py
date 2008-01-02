# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains ASCII import/export functions.
"""

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

def parse(f, column_names=None, separator=",", qualifier='"'):
	for line in f:
		yield parse_line(line, column_names, separator, qualifier)

def parse_line(line, column_names=None, separator=",", qualifier='"'):
	fields = []
	buff = ''
	infield = False
	qualignore = False
	
	for i in range(len(line)):
		c = line[i]
		if(c == qualifier):
			if(infield):
				if(i < len(line) - 1 and line[i + 1] == qualifier):
					if(qualignore):
						qualignore = False
					else:
						qualignore = True
						buff += c
				else:
					infield = False
			else:
				if(qualignore):
					qualignore = False
				else:
					infield = True
		elif(c == separator):
			if(infield):
				buff += c
			else:
				fields.append(buff)
				buff = ''
		else:
			buff += c
	
	if(buff):
		fields.append(buff)
	
	if(column_names == None):
		return fields
	
	return dict(zip(column_names, fields))
