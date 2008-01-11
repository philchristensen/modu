#!/usr/bin/python

# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id: __init__.py 437 2007-08-14 20:26:01Z phil $
#
# See LICENSE for details

import os, os.path

from distutils.core import setup

modu_path = os.path.join(os.path.dirname(__file__), 'modu')
assets_path = os.path.join(modu_path, 'assets')
skel_path = os.path.join(modu_path, 'skel')

def load_paths(path):
	paths = []
	for dirpath, dirnames, filenames in os.walk(path):
		if(dirpath.find('.svn') != -1):
			continue
		if('fckeditor' in dirnames):
			dirnames.remove('fckeditor')
			paths.append(os.path.join(dirpath[len(modu_path) + 1:], 'fckeditor/README.FCKEditor'))
		for f in filenames:
			if(f.startswith('.')):
				continue
			paths.append(os.path.join(dirpath[len(modu_path) + 1:], f))
	return paths

dist = setup(name="modu",
			 version="0.9",
			 description="pragmatic web framework",
			 author="Phil Christensen",
		 	 author_email="phil@bubblehouse.org",
			 url="http://modu.bubblehouse.org",
			 packages=['modu', 'modu.editable', 'modu.editable.datatypes', 
						'modu.itemdefs', 'modu.persist', 'modu.sites', 
						'modu.test', 'modu.util', 'modu.web', 'twisted.plugins'],
			scripts=['bin/mkmodu.py'],
			package_data={'modu': load_paths(assets_path) + load_paths(skel_path)},
			)
