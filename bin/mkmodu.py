#!/usr/bin/env python

# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
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

import os.path, sys

import warnings
warnings.simplefilter('ignore', UserWarning)

from twisted.python import usage

from modu import skel

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
	
	shortname = config['shortname']
	if not config['longname']:
		config['longname'] = config['shortname']
	if not config['author']:
		config['author'] = config['shortname']
	del config['shortname']
	
	skel.create_project(shortname, destroot, **config)
	
	print "Created skeleton `%s` project in %s" % (shortname, destroot) 
