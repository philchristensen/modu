# modusite
# Copyright (C) 2007 Phil Christensen
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
	
	head_tarball_path   = string.StringField(
		label			= 'SVN head tarball:',
		weight			= 2,
	),
	
	teaser				= string.TextAreaField(
		label			= 'teaser:',
		weight			= 4,
		height			= 150,
	),
	
	body				= string.TextAreaField(
		label			= 'page body:',
		weight			= 5
	),
	
	active				= boolean.CheckboxField(
		label			= 'active:',
		weight			= 8
	)
)