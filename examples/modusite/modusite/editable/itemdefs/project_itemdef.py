# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

from modu import util
from modu.editable import define
from modu.editable.datatypes import string, boolean, fck
from modu.editable.datatypes import select, relational, date

__itemdef__ = define.itemdef(
	__config			= dict(
		name			= 'project',
		label			= 'projects',
		acl				= 'access admin',
		category		= 'site content',
		weight			= 2
	),
	
	id					= string.LabelField(
		label			= 'id:',
		weight			= -10,
		listing			= True
	),
	
	name				= string.StringField(
		label			= 'name:',
		size			= 60,
		maxlength 		= 255,
		weight			= 1,
		listing			= True,
		link			= True,
		search			= True
	),
	
	license_name		= string.StringField(
		label			= 'license name:',
		weight			= 2,
		listing			= True,
	),
	
	license_url			= string.StringField(
		label			= 'license url:',
		weight			= 3,
	),
	
	installation_url	= string.StringField(
		label			= 'installation url:',
		weight			= 4,
	),
	
	changelog_url		= string.StringField(
		label			= 'changelog url:',
		weight			= 5,
	),
	
	tarball_url			= string.StringField(
		label			= 'tarball url:',
		weight			= 6,
	),
	
	tarball_checksum	= string.StringField(
		label			= 'tarball checksum:',
		weight			= 7,
	),
	
	active				= boolean.CheckboxField(
		label			= 'active:',
		weight			= 8
	)
)
