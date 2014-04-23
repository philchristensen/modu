# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
Utilities to create stub files for a modu project.
"""

import os, os.path, time

import pkg_resources as pkg

from Cheetah.Template import Template

def create_project(shortname, dest, path='skel', **config):
	for filename in pkg.resource_listdir('modu', path):
		if(filename.startswith('__init__.py')):
			continue
		
		resource_path = os.path.join(path, filename)
		
		if(pkg.resource_isdir('modu', resource_path)):
			directory = filename
			if(directory.startswith('.')):
				continue
			if(directory.startswith('project')):
				directory = directory.replace('project', shortname)
			
			new_dest = os.path.join(dest, directory)
			
			if not(os.path.isdir(new_dest)):
				os.makedirs(new_dest)
			create_project(shortname, new_dest, resource_path, **config)
		else:
			if(filename.startswith('.')):
				continue
			
			new_file = None
			output_file = None
			file_stream = pkg.resource_stream('modu', resource_path)
			try:
				if(filename.endswith('.tmpl')):
					template_class = Template.compile(file=file_stream)
					
					variables = dict(
						project_name = shortname,
						project_description = config.get('longname', shortname),
						copyright_holder = config.get('author', shortname),
						year = time.strftime('%Y')
					)
					
					output = str(template_class(searchList=[variables]))
					new_filename = filename[:-5]
					if(new_filename.startswith('project')):
						new_filename = new_filename.replace('project', shortname)
					new_path = os.path.join(dest, new_filename)
					
					new_file = open(new_path, 'w')
					new_file.write(output)
					new_file.close()
				else:
					# copy the file
					output_filename = os.path.join(dest, filename)
					output_file = open(output_filename, 'w')
					shutil.copyfileobj(file_stream, output_file)
					output_file.close()
			finally:
				if(new_file and not new_file.closed):
					new_file.close()
				if(output_file and not output_file.closed):
					output_file.close()
				file_stream.close()

