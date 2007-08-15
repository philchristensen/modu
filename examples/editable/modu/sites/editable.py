# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import classProvides, implements

from twisted import plugin

from modu.web.app import ISite
from modu.web import editable
from modu.persist import storable

class EditablePage(storable.Storable):
	implements(editable.IEditable)
	
	def __init__(self):
		super(EditablePage, self).__init__('page')

	def get_itemdef(self):
		return editable.itemdef(
			id				= editable.definition(
				type		= 'LabelField',
				label		= 'id:',
				size		= 10,
				help		= 'the id of this page.',
				list		= True,
				weight		= 0
			),
			
			title			= editable.definition(
				type		= 'StringField',
				label		= 'title:',
				size		= 60,
				maxlength 	= 64,
				help		= 'the title of this page.',
				list		= True,
				weight		= 1
			),
			
			code			= editable.definition(
				type		= 'StringField',
				label		= 'code:',
				size		= 40,
				help		= 'the URL code of this page.',
				list		= True,
				weight		= 2
			),
			
			content			= editable.definition(
				type		= 'TextAreaField',
				label		= 'content:',
				help		= 'the content of the page.',
				weight		= 3,
				rows		= 10,
				cols		= 70
			),
			
			created_date	= editable.definition(
				type		= 'DateField',
				label		= 'created date:',
				datatype	= 'timestamp',
				help		= 'the date this page was created.',
				list		= True,
				weight		= 4
			),
			
			modified_date	= editable.definition(
				type		= 'DateField',
				label		= 'modified date:',
				datatype	= 'timestamp',
				help		= 'the date this page was created.',
				list		= True,
				default_now = True,
				weight		= 5
			)
		)


class EditableSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, application):
		application.base_path = '/editable'
		application.base_domain = 'localhost'
		application.activate(editable.EditorResource())
		
	def configure_request(self, req):
		req.store.ensure_factory('page', EditablePage)