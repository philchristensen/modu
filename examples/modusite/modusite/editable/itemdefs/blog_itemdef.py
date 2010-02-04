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

def update_published_by(req, form, storable):
	if not(getattr(storable, 'published_by', None)):
		storable.published_by = req.user.get_id()
		output = req.user.first + ' ' + req.user.last
		form['published_by'](value=storable.published_by)
	return True

__itemdef__ = define.itemdef(
	__config			= dict(
		name			= 'blog',
		label			= 'blog entries',
		acl				= 'access admin',
		category		= 'site content',
		prewrite_callback = update_published_by,
		weight			= 1
	),
	
	id					= string.LabelField(
		label			= 'id:',
		weight			= -10,
		listing			= True
	),
	
	title				= string.StringField(
		label			= 'title:',
		size			= 60,
		maxlength 		= 255,
		weight			= 1,
		listing			= True,
		link			= True,
		search			= True
	),
	
	category_code		= string.StringField(
		label			= 'category:',
		size			= 60,
		maxlength 		= 255,
		weight			= 2,
		listing			= True,
		link			= True,
		search			= True
	),
	
	teaser				= fck.FCKEditorField(
		label			= 'teaser:',
		weight			= 4,
		height			= 150,
		toolbar_set		= 'Basic'
	),
	
	body				= fck.FCKEditorField(
		label			= 'page body:',
		weight			= 5
	),
	
	published_by		= relational.ForeignSelectField(
		label			= 'author:',
		fvalue			= 'id',
		flabel			= 'username',
		ftable			= 'user',
		help			= 'This field is filled/updated automatically when the record is saved.',
		weight			= 6
	),
	
	published_date		= date.DateField(
		label			= 'published date:',
		style			= 'datetime',
		default_now		= True,
		save_format		= 'datetime',
		weight			= 7
	),
	
	active				= boolean.CheckboxField(
		label			= 'active:',
		weight			= 8
	)
)
