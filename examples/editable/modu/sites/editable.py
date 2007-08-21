# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import classProvides, implements

from twisted import plugin

from modu.web.app import ISite
from modu.web import resource
from modu.persist import storable
from modu.datatypes import string, relational

class EditablePage(storable.Storable):
	def __init__(self):
		super(EditablePage, self).__init__('page')

	def get_itemdef(self):
		return define.itemdef(
			id				= string.LabelField(
				label		= 'id:',
				size		= 10,
				help		= 'the id of this page.',
				list		= True,
				weight		= -10
			),
			
			title			= string.StringField(
				label		= 'title:',
				size		= 60,
				maxlength 	= 64,
				help		= 'the title of this page.',
				list		= True,
				weight		= 0
			),
			
			password		= string.PasswordField(
				type		= 'PasswordField',
				label		= 'password:',
				help		= 'a password for this page.',
				weight		= 1
			),
			 
			category_id		= relational.ForeignAutocompleteField(
				label		= 'category:',
				help		= 'a category for this page.',
				url			= '/editable/autocomplete/page/category_id',
				fvalue		= 'id',
				flabel		= 'title',
				ftable		= 'category',
				weight		= 2
			),
			 
			other_categories= relational.ForeignMultipleAutocompleteField(
				label		= 'other categories:',
				help		= 'additional categories for this page.',
				url			= '/editable/autocomplete/page/other_categories',
				fvalue		= 'id',
				flabel		= 'title',
				ftable		= 'category',
				ntof		= 'page_category',
				ntof_f_id	= 'category_id',
				ntof_n_id	= 'page_id',
				weight		= 2
			),
			 
			code			= string.StringField(
				label		= 'code:',
				size		= 40,
				help		= 'the URL code of this page.',
				list		= True,
				weight		= 3
			),
			
			content			= string.TextAreaField(
				label		= 'content:',
				help		= 'the content of the page.',
				weight		= 4,
				rows		= 10,
				cols		= 70
			),
			
			created_date	= string.DateField(
				label		= 'created date:',
				datatype	= 'timestamp',
				help		= 'the date this page was created.',
				list		= True,
				weight		= 5
			),
			
			modified_date	= string.DateField(
				label		= 'modified date:',
				datatype	= 'timestamp',
				help		= 'the date this page was created.',
				list		= True,
				default_now = True,
				weight		= 6
			)
		)


class EditableSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, application):
		application.base_path = '/editable'
		application.base_domain = 'localhost'
		application.activate(editable.EditorResource())
		
		import os.path, modu
		
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(resource.FileResource(['/assets'], modu_assets_path))
		
	def configure_request(self, req):
		req.store.ensure_factory('page', EditablePage)