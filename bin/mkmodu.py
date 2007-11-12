#!/usr/bin/env python

import os, os.path, sys, time

from twisted.python import usage

from Cheetah.Template import Template

class Options(usage.Options):
	optParameters = [["longname", "l", None, "The descriptive name for the new project."],
					 ["author", "a", None, "Name of copyright holder."]
					]
	
	synopsis = 'Usage: mkmodu.py project [options]'
	
	def parseArgs(self, shortname):
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
	
	skelroot = os.path.normpath(os.path.dirname(__file__) + '/../skel')
	
	destroot = os.path.normpath(config['shortname'])
	
	for dirpath, dirnames, filenames in os.walk(skelroot):
		print (dirpath, dirnames, filenames)
		created_dir = os.path.join(destroot, dirpath[5:])
		os.mkdir(created_dir)
		
		for filename in filenames:
			if(filename.startswith('.')):
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
				newfile = os.path.join(created_dir, filename[:-5])
				
				nf = open(newfile, 'w')
				nf.write(output)
				nf.close()
			else:
				# copy the file
				pass
