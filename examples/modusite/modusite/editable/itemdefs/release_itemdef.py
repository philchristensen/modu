# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

import os, os.path

from modu import util
from modu.editable import define
from modu.editable.datatypes import string, boolean, fck
from modu.editable.datatypes import select, relational, date

def get_checksum(filepath, md5_path='md5sum'):
	handle = os.popen(md5_path + ' "' + filepath.replace(r';', r'\;') + '"')
	filehash = handle.read()
	handle.close()
	
	if(filehash.find('=') == -1):
		filehash = [output.strip() for output in filehash.split(' ')][0]
	else:
		filehash = [output.strip() for output in filehash.split('=')][1]
	
	return filehash

def release_prewrite_callback(req, frm, storable):
	filename = getattr(storable, 'filename', '')
	if(filename.endswith('.tar.gz')):
		full_path = os.path.join(req.app.release_path, filename)
		md5_path = req.app.config.get('md5_path', 'md5sum')
		if not(getattr(storable, 'tarball_url', None)):
			storable.tarball_url = req.get_path('releases', filename)
			storable.tarball_checksum = get_checksum(full_path, md5_path=md5_path)
	
	return True

__itemdef__ = define.itemdef(
	__config				= dict(
		name				= 'release',
		label				= 'releases',
		acl					= 'access admin',
		category			= 'site content',
		prewrite_callback	= release_prewrite_callback,
		weight				= 4,
	),
	
	id					= string.LabelField(
		label			= 'id:',
		weight			= -10,
		listing			= True,
	),
	
	project_id			= relational.ForeignSelectField(
		label			= 'related project:',
		ftable			= 'project',
		fvalue			= 'id',
		flabel			= 'name',
		weight			= 1,
		listing			= True,
	),
	
	version_weight		= string.StringField(
		label			= 'version weight:',
		size			= 5,
		weight			= 2,
		listing			= True,
		help			= 'The release version will be sorted by this string.',
	),
	
	version_string		= string.StringField(
		label			= 'version string:',
		size			= 10,
		weight			= 3,
		listing			= True,
		help			= 'This is the version info that is actually displayed',
	),
	
	filename			= fck.FCKFileField(
		label			= 'filename:',
		fck_root		= '/fck/releases',
		listing			= True,
		link			= True,
		weight			= 4,
	),
	
	tarball_url			= string.StringField(
		label			= 'tarball url:',
		weight			= 5,
	),
	
	tarball_checksum	= string.StringField(
		label			= 'tarball checksum:',
		weight			= 6,
	),
	
	description			= string.TextAreaField(
		label			= 'page body:',
		weight			= 7,
	),
	
	nightly				= boolean.CheckboxField(
		label			= 'nightly:',
		weight			= 7.5,
		default_checked	= False,
	),
	
	active				= boolean.CheckboxField(
		label			= 'active:',
		weight			= 8,
		default_checked	= True,
	),
	
	license_name		= string.StringField(
		label			= 'license name:',
		weight			= 9,
		listing			= True,
	),
	
	license_url			= string.StringField(
		label			= 'license url:',
		weight			= 10,
	),
	
	installation_url	= string.StringField(
		label			= 'installation url:',
		weight			= 11,
	),
	
	changelog_url		= string.StringField(
		label			= 'changelog url:',
		weight			= 12,
	),
)
