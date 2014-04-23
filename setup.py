# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

import ez_setup
ez_setup.use_setuptools()

import sys, os, os.path

try:
	from twisted import plugin
	from twisted.python.reflect import namedAny
except ImportError, e:
	print >>sys.stderr, "setup.py requires Twisted to create a proper modu installation. Please install it before continuing."
	sys.exit(1)

from setuptools import setup, find_packages
from setuptools.command import easy_install
import pkg_resources as pkgrsrc

from distutils import log
log.set_threshold(log.INFO)

os.environ['COPY_EXTENDED_ATTRIBUTES_DISABLE'] = 'true'
os.environ['COPYFILE_DISABLE'] = 'true'

def autosetup():
	pluginPackages = ['twisted.plugins', 'modu.sites']
	
	dist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
	sys.path.insert(0, dist_dir)
	regeneratePluginCache(pluginPackages)
	
	dist = setup(
		name			= "modu",
		version			= "1.0.3",
		packages		= find_packages('src') + ['twisted'],
		package_dir		= {'':'src'},
		test_suite		= "modu.test",
		scripts			= ['bin/mkmodu.py'],
		
		zip_safe		= False,
		
		install_requires = ["Twisted>=9.0.0", "MySQL-python>=1.2.3c1", "Cheetah>=2.4.1"],
		
		include_package_data = True,
		package_data = {
			''			: ['ChangeLog', 'ez_setup.py', 'INSTALL', 'LICENSE', 'README'],
			'twisted'	: ['plugins/modu_web.py'],
		},
		
		# metadata for upload to PyPI
		author			= "Phil Christensen",
		author_email	= "phil@bubblehouse.org",
		description		= "pragmatic web framework",
		license			= "MIT",
		keywords		= "modu wsgi www http web framework",
		url				= "http://modu.bubblehouse.org",
		download_url	= "http://modu.bubblehouse.org/blog/modu-version-1-0-released",
		# could also include long_description, download_url, classifiers, etc.
		long_description = """modu is a high-level toolkit for building database-driven 
								web applications in Python. It provides all the common 
								components needed to build custom web applications in 
								Python, including form generation, object-relational 
								database mapping support, pluggable template systems, 
								database-resident session and user support, and more.
							""".replace('\t', '')
	)
	
	return dist

def pluginModules(moduleNames):
	for moduleName in moduleNames:
		try:
			yield namedAny(moduleName)
		except ImportError:
			pass
		except ValueError, ve:
			if ve.args[0] != 'Empty module name':
				import traceback
				traceback.print_exc()
		except:
			import traceback
			traceback.print_exc()

def regeneratePluginCache(pluginPackages):
	print 'Regenerating plugin cache...'
	for pluginModule in pluginModules(pluginPackages):
		plugin_gen = plugin.getPlugins(plugin.IPlugin, pluginModule)
		try:
			plugin_gen.next()
		except StopIteration, e:
			pass
		except TypeError, e:
			print 'TypeError: %s' % e

if(__name__ == '__main__'):
	__dist__ = autosetup()
