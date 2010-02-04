# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

import ez_setup
ez_setup.use_setuptools()

import sys, os, pprint, traceback

from setuptools import setup, find_packages

def autosetup():
	pluginPackages = []

	for (dirpath, dirnames, filenames) in os.walk(os.curdir):
		dirnames[:] = [p for p in dirnames if not p.startswith('.')]
		pkgName = dirpath[2:].replace('/', '.')
		if 'plugins' in dirnames:
			# The current directory is for the Twisted plugin system
			pluginPackages.append(pkgName)

	dist = setup(
		name			= "modu",
		version			= "1.0",
		packages		= find_packages('src') + ['twisted'],
		package_dir		= {'':'src'},
		test_suite		= "modu.test",
		scripts			= ['bin/mkmodu.py'],
	
		zip_safe		= True,
	
		install_requires = ['Twisted>=9.0.0'],
		extras_require = {
			'mysql'		: ["MySQL-python>=1.2.3c1"],
			'cheetah'	: ["Cheetah>=2.4.1"],
		},
	
		include_package_data = True,
		package_data = {
			''			: ['ChangeLog', 'ez_setup.py', 'INSTALL', 'LICENSE', 'README'],
			'twisted'	: ['plugins/modu_web.py', 'plugins/dropin.cache'],
		},
	
		# metadata for upload to PyPI
		author			= "Phil Christensen",
		author_email	= "phil@bubblehouse.org",
		description		= "pragmatic web framework",
		license			= "MIT",
		keywords		= "modu wsgi www http web framework",
		url				= "http://modu.bubblehouse.org",
		download_url	= "http://modu.bubblehouse.org/downloads",
		# could also include long_description, download_url, classifiers, etc.
		long_description = """modu is a high-level toolkit for building database-driven 
								web applications in Python. It provides all the common 
								components needed to build custom web applications in 
								Python, including form generation, object-relational 
								database mapping support, pluggable template systems, 
								database-resident session and user support, and more.
							""".replace('\t', '')
	)
	
	regeneratePluginCache(dist, pluginPackages)
	
	return dist

def pluginModules(moduleNames):
	from twisted.python.reflect import namedAny
	for moduleName in moduleNames:
		try:
			yield namedAny(moduleName)
		except ImportError:
			pass
		except ValueError, ve:
			if ve.args[0] != 'Empty module name':
				traceback.print_exc()
		except:
			traceback.print_exc()

def _regeneratePluginCache(pluginPackages):
	print 'Regenerating cache with path: ',
	pprint.pprint(sys.path)
	from twisted import plugin
	for pluginModule in pluginModules([
		p + ".plugins" for p in pluginPackages]):
		# Not just *some* zigs, mind you - *every* zig:
		print 'Full plugin list for %r: ' % (pluginModule.__name__)
		pprint.pprint(list(plugin.getPlugins(plugin.IPlugin, pluginModule)))

def regeneratePluginCache(dist, pluginPackages):
	if 'install' in dist.commands:
		sys.path.insert(0, os.path.abspath(dist.command_obj['install'].install_lib))
		_regeneratePluginCache(pluginPackages)

__dist__ = autosetup()
