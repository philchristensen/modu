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

import os, os.path, sys, time
import pkg_resources as pkg

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
	
	destroot = os.path.abspath(os.path.normpath(config['shortname']))
	
	config['shortname'] = os.path.basename(destroot)
	
	if not config['longname']:
		config['longname'] = config['shortname']
	if not config['author']:
		config['author'] = config['shortname']
	
	def copy_skel(path, dest):
		#import pdb
		for filename in pkg.resource_listdir('modu', path):
			resource_path = os.path.join(path, filename)
			
			if(pkg.resource_isdir('modu', resource_path)):
				directory = filename
				if(directory.startswith('.')):
					continue
				if(directory.startswith('project')):
					directory = directory.replace('project', config['shortname'])
				
				new_dest = os.path.join(dest, directory)
				
				if not(os.path.isdir(new_dest)):
					os.makedirs(new_dest)
				#pdb.set_trace()
				copy_skel(resource_path, new_dest)
			else:
				if(filename.startswith('.')):
					continue
				
				with pkg.resource_stream('modu', resource_path) as file_stream:
					if(filename.endswith('.tmpl')):
						template_class = Template.compile(file=file_stream)
						
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
						new_path = os.path.join(dest, new_filename)
						
						#pdb.set_trace()
						with open(new_path, 'w') as new_file:
							new_file.write(output)
					else:
						# copy the file
						output_filename = os.path.join(dest, filename)
						#pdb.set_trace()
						with open(output_filename, 'w') as output_file:
							shutil.copyfileobj(file_stream, output_file)
	
	copy_skel('skel', destroot)
