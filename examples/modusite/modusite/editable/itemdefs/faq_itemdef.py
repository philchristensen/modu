# modusite
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#

from modu import util
from modu.editable import define
from modu.editable.datatypes import string, boolean, fck
from modu.editable.datatypes import select, relational, date

def update_answered_by(req, form, storable):
	if not(getattr(storable, 'answered_by', None)):
		storable.answered_by = req.user.get_id()
		output = req.user.first + ' ' + req.user.last
		form['answered_by'](value=storable.answered_by)
	return True

__itemdef__ = define.itemdef(
	__config			= dict(
		name			= 'faq',
		label			= 'FAQs',
		acl				= 'access admin',
		category		= 'site content',
		prewrite_callback = update_answered_by,
		weight			= 1
	),
	
	id					= string.LabelField(
		label			= 'id:',
		weight			= -10,
		listing			= True
	),
	
	question				= string.TextAreaField(
		label			= 'question:',
		weight			= 1,
		listing			= True,
		link			= True,
		search			= True
	),
	
	answer				= string.TextAreaField(
		label			= 'answer:',
		weight			= 5
	),
	
	answered_by		= relational.ForeignSelectField(
		label			= 'answered by:',
		fvalue			= 'id',
		flabel			= 'username',
		ftable			= 'user',
		help			= 'This field is filled/updated automatically when the record is saved.',
		weight			= 6
	),
	
	answered_date		= date.DateField(
		label			= 'answered date:',
		style			= 'date',
		default_now		= True,
		save_format		= 'datetime',
		weight			= 7
	),
	
	weight				= string.StringField(
		label			= 'weight:',
		size			= 5,
		weight			= 8,
		attributes		= dict(value=0)
	)
)
