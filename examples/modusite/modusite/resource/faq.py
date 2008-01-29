# modusite
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#

from modu.web import resource, app
from modu.persist import storable

class Resource(resource.CheetahTemplateResource):
	def get_paths(self):
		"""
		@see: L{modu.web.resource.IResource.get_paths()}
		"""
		return ['/faq']
	
	def prepare_content(self, req):
		"""
		@see: L{modu.web.resource.IContent.prepare_content()}
		"""
		faqs = req.store.load(storable.Storable('faq'))
		
		self.set_slot('title', 'modu: faq')
		self.set_slot('faqs', faqs)
	
	def get_content_type(self, req):
		"""
		@see: L{modu.web.resource.IContent.get_content_type()}
		"""
		return 'text/html; charset=UTF-8'
	
	def get_template(self, req):
		"""
		@see: L{modu.web.resource.ITemplate.get_template()}
		"""
		return 'faq.html.tmpl'

