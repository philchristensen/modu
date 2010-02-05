# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

import urllib

from modu.editable import define
from modu.util import form, tags
from modu.persist import sql

from modusite.model import release

class ReleaseListField(define.definition):
	"""
	Display a list of releases for the current project.
	"""
	def get_element(self, req, style, storable):
		frm = form.FormNode(self.name)
		project_id = storable.get_id()
		
		if not(project_id):
			frm['release'](
				type	= 'label',
				value	= "You must save this project before adding a new release.",
			)
			return frm
		
		req.store.ensure_factory('release', model_class=release.Release)
		
		releases = req.store.load('release', project_id=project_id, __order_by='version_weight DESC') or []
		
		query = {
			'__init__[project_id]'			: storable.get_id(),
			'__init__[license_name]'		: storable.license_name,
			'__init__[license_url]'			: storable.license_url,
			'__init__[installation_url]'	: storable.installation_url,
			'__init__[changelog_url]'		: storable.changelog_url,
		}
		
		new_release_url = req.get_path(req.prepath, 'detail/release/new?' + urllib.urlencode(query))
		
		if not(releases):
			if(style == 'listing'):
				frm['release'](
					type	= 'label',
					value	= "(no releases)",
				)
			else:
				frm['release'](
					type	= 'label',
					value	= "This project has no releases yet. " +
								tags.a(href=new_release_url)['Click here to create one.'],
				)
			return frm
		
		for r in releases:
			release_url = req.get_path(req.prepath, 'detail/release', r.get_id())
			frm['release'][r.get_id()](
				prefix = '<span class="releases">',
				suffix = '</span>',
			)
			frm['release'][r.get_id()]['version_string'](
				type 	= 'label',
				value	= tags.a(href=release_url)[r.version_string],
			)
		
		if(style != 'listing'):
			frm['release']['new'](
				type	= 'markup',
				prefix	= '<div>',
				value	= tags.a(href=new_release_url)['Create New Release'],
				suffix	= '</div>',
			)
		
		return frm
	
	def update_storable(self, req, form, storable):
		"""
		No operation.
		
		@see: L{modu.editable.define.definition.update_storable()}
		"""
		pass