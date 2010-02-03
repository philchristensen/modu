# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages

setup(
	name			= "modu",
	version 		= "1.0",
	packages		= find_packages('src'),
	package_dir		= {'':'src'},
	scripts 		= ['bin/mkmodu.py'],
	
	install_requires 		= ['twisted'],
	include_package_data 	= True,
	
	package_data	= {
		''			: ['ChangeLog', 'ez_setup.py', 'INSTALL', 'LICENSE', 'README'],
		'twisted'	: ['plugins/modu_web.py'],
	},
	
	# metadata for upload to PyPI
	author = "Phil Christensen",
	author_email = "phil@bubblehouse.org",
	description = "pragmatic web framework",
	license = "BSD",
	keywords = "modu wsgi www http web framework",
	url = "http://modu.bubblehouse.org",

	# could also include long_description, download_url, classifiers, etc.
)
