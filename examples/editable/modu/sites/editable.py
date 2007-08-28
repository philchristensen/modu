# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope.interface import classProvides

from twisted import plugin

from modu.web.app import ISite
from modu.web import resource, static
from modu.persist import storable
from modu.editable.datatypes import string, relational

class EditorResource(resource.CheetahTemplateResource):
	"""
	A basic editor resource. Displays editors for any registered
	IEditable-instantiating Factory.
	"""
	def get_paths(self):
		return ['/edit', '/autocomplete']
	
	def prepare_content(self, req):
		if not(len(req.app.tree.postpath) >= 2):
			app.raise404('/'.join(req.app.tree.postpath))
		if not(req.store.has_factory(req.app.tree.postpath[0])):
			app.raise500('No registered factory for %s' % req.app.tree.postpath[0])
		
		if(req.app.tree.prepath[0] == 'autocomplete'):
			self.prepare_autocomplete(req)
		else:
			self.prepare_editor(req)
	
	def prepare_autocomplete(self, req):
		item = req.store.load_one(req.app.tree.postpath[0], {}, __limit=1)
		if not(IEditable.providedBy(item)):
			app.raise500('%r is does not implement the IEditable interface.')
		
		itemdef = item.get_itemdef()
		definition = itemdef[req.app.tree.postpath[1]]
		post_data = form.NestedFieldStorage(req)
		results = []
		
		if('q' in post_data):
			partial = post_data['q'].value
		else:
			partial = None
		
		if(partial):
			if(definition.get('autocomplete_callback')):
				results = definition['autocomplete_callback'](partial, definition, item)
			else:
				value = definition['fvalue']
				label = definition['flabel']
				table = definition['ftable']
			
				ac_query = "SELECT %s, %s FROM %s WHERE %s LIKE %%s" % (value, label, table, label)
			
				results = req.store.pool.runQuery(ac_query, ['%%%s%%' % partial])
		
		content = ''
		for result in results:
			content += "%s|%d\n" % (result[label], result[value])
		
		app.raise200([('Content-Type', 'text/plain')], [content])
	
	def prepare_editor(self, req):
		item = req.store.load_one(req.app.tree.postpath[0], {'id':int(req.app.tree.postpath[1])})
		if not(IEditable.providedBy(item)):
			app.raise500('%r is does not implement the IEditable interface.')
		
		form = item.get_itemdef().get_form(item)
		if(form.execute(req)):
			form = item.get_itemdef().get_form(item)
		
		self.set_slot('form', form.render(req))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'editable-detail.html.tmpl' 


class EditableSite(object):
	classProvides(plugin.IPlugin, ISite)
	
	def initialize(self, application):
		application.base_path = '/modu/examples/editable'
		application.base_domain = 'localhost'
		application.activate(EditorResource())
		
		import os.path, modu
		
		modu_assets_path = os.path.join(os.path.dirname(modu.__file__), 'assets')
		application.activate(static.FileResource(['/assets'], modu_assets_path))
