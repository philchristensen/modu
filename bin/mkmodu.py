#!/usr/bin/env python

# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Generate a modu project directory.

This script creates a directory structure for a new modu project. It
is assumed that the resulting directory will act as the approot in
the new application, and that the directory will be added to the
Python search path, either globally, or by a web container-specific
directive.
"""

import modu

import os, os.path, sys, time

from twisted.python import usage

from Cheetah.Template import Template

class Options(usage.Options):
	"""
	Implement usage parsing for the mkmodu script.
	"""
	optParameters = [["longname", "l", None, "The descriptive name for the new project."],
					 ["author", "a", None, "Name of copyright holder."]
					]
	
	synopsis = 'Usage: mkmodu.py project [options]'
	
	def parseArgs(self, shortname):
		"""
		Implement the required `shortname` argument.
		"""
		self['shortname'] = shortname

if(__name__ == '__main__'):
	config = Options()
	try:
		config.parseOptions()
	except usage.UsageError, e:
		print config.getSynopsis()
		print config.getUsage()
		print e.args[0]
		sys.exit(1)
	
	skelroot = os.path.join(os.path.dirname(modu.__file__), 'skel')
	destroot = os.path.abspath(os.path.normpath(config['shortname']))
	
	config['shortname'] = os.path.basename(destroot)
	
	if not config['longname']:
		config['longname'] = config['shortname']
	if not config['author']:
		config['author'] = config['shortname']
	
	for dirpath, dirnames, filenames in os.walk(skelroot):
		stub = dirpath[len(skelroot) + 1:]
		if(stub.startswith('.')):
			continue
		if(stub.find('.svn') != -1):
			continue
		if(stub.startswith('project')):
			stub = stub.replace('project', config['shortname'])
		created_dir = os.path.join(destroot, stub)
		
		os.mkdir(created_dir)
		
		for filename in filenames:
			if(filename.startswith('.')):
				continue
			elif(filename.find('.svn') != -1):
				continue
			elif(filename.endswith('.tmpl')):
				template_path = os.path.join(dirpath, filename)
				template_class = Template.compile(file=open(template_path))
				
				variables = dict(
					project_name = config['shortname'],
					project_description = config.get('longname', config['shortname']),
					copyright_holder = config.get('author', config['shortname']),
					year = time.strftime('%Y')
				)
				
				output = str(template_class(searchList=[variables]))
				new_filename = filename[:-5]
				if(new_filename.startswith('project')):
					new_filename = new_filename.replace('project', config['shortname'])
				newfile = os.path.join(created_dir, new_filename)
				
				nf = open(newfile, 'w')
				nf.write(output)
				nf.close()
			else:
				# copy the file
				pass
