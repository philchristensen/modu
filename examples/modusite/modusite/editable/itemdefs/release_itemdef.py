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
		name			= 'release',
		label			= 'releases',
		acl				= 'access admin',
		category		= 'site content',
		weight			= 4
	),
	
	id					= string.LabelField(
		label			= 'id:',
		weight			= -10,
		listing			= True
	),
	
	project_id			= relational.ForeignSelectField(
		label			= 'related project:',
		ftable			= 'project',
		fvalue			= 'id',
		flabel			= 'name',
		weight			= 1,
		listing			= True
	),
	
	version_id			= string.StringField(
		label			= 'version id:',
		size			= 5,
		weight			= 3,
		listing			= True,
		help			= 'This functions like a version "weight", and is how version numbers are compared.'
	),
	
	version_string		= string.StringField(
		label			= 'version string:',
		size			= 10,
		weight			= 4,
		listing			= True,
		help			= 'This is the version info that is actually displayed'
	),
	
	filename			= string.StringField(
		label			= 'filename:',
		size			= 60,
		maxlength 		= 255,
		weight			= 4.5
	),
	
	description			= string.TextAreaField(
		label			= 'page body:',
		weight			= 5
	),
	
	active				= boolean.CheckboxField(
		label			= 'active:',
		weight			= 8
	)
)
