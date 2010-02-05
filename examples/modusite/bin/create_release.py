#!/usr/bin/env python

# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Generate a release tarball.
"""

import sys, os.path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from twisted.python import usage

from modusite.scripts import release

class Options(usage.Options):
	"""
	Implement usage parsing for the create_nightly script.
	"""
	synopsis = 'Usage: create_release.py source-dir release-dir [options]'
	
	optFlags = [
		["nightly", "n", "Generate a nightly tarball."],
	]
	
	def parseArgs(self, source_dir, release_dir):
		"""
		Store the required arguments.
		"""
		self['source-dir'] = os.path.abspath(source_dir)
		self['release-dir'] = os.path.abspath(release_dir)

if(__name__ == '__main__'):
	config = Options()
	try:
		config.parseOptions()
	except usage.UsageError, e:
		print >>sys.stderr, config.getSynopsis()
		print >>sys.stderr, config.getUsage()
		print >>sys.stderr, e.args[0]
		sys.exit(1)
	
	try:
		release.create(config['source-dir'], config['release-dir'], nightly=config['nightly'])
	except Exception, e:
		print >>sys.stderr, '%s: %s' % (e.__class__.__name__, e)