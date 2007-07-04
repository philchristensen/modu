# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope import interface
from zope.interface import implements

class IController(interface.Interface):
	"""
	This class defines something that reacts when a path is req.
	"""
	def get_paths(self):
		"""
		Return all paths that this controller supports.
		"""
	
	def get_response(self, req):
		"""
		Do whatever this thing should do when a path is loaded.
		"""
		raise NotImplementedError('%s::get_response()' % self.__class__.__name__)

class IContent(interface.Interface):
	"""
	This class represents a piece of content that has a MIME-type of some kind.
	"""
	def prepare_content(self, req):
		"""
		Run any neccessary code that prepares this content object for display.
		This method is only called once.
		"""
	
	def get_content(self, req):
		"""
		Return the content for this item. This method can be called multiple times,
		but is always called **after** prepare_content()
		"""
	
	def get_content_type(self, req):
		"""
		Return the mime type of this content.
		"""

class Resource(object):
	implements(IController, IContent)
	
	def get_response(self, req):
		self.prepare_content(req)
		req['modu.app'].add_header('Content-Type', self.get_content_type(req))
		content = self.get_content(req)
		req['modu.app'].add_header('Content-Length', len(content))
		return content

class TemplateContent(object):
	implements(IContent)
	
	def set_slot(self, name, value):
		if not(hasattr(self, 'data')):
			self.data = {}
		self.data[name] = value
	
	def get_content(self, req):
		import string
		engine = string.Template(self.get_template(req))
		return engine.safe_substitute(self.data)
	
	def get_content_type(self, req):
		return 'text/html'

class CheetahTemplateContent(TemplateContent):
	"""http://www.cheetahtemplate.org"""
	def get_content(self, req):
		from Cheetah.Template import Template
		template_file = open(req['modu.approot'] + '/template/' + self.get_template(req))
		self.template = Template(file=template_file, searchList=[self.data])
		return str(self.template)

class ZPTemplateContent(TemplateContent):
	"""http://zpt.sourceforge.net"""
	def get_content(self, req):
		from ZopePageTemplates import PageTemplate
		class ZPTmoduTemplate(PageTemplate):
			def __call__(self, context={}, *args):
				if not context.has_key('args'):
					context['args'] = args
				return self.pt_render(extra_context=context)
		template_file = open(req['modu.approot'] + '/template/' + self.get_template(req))
		self.template = ZPTmoduTemplate()
		self.template.write(template_file.read())
		return self.template(context={'here':self.data})

class CherryTemplateContent(TemplateContent):
	"""http://cherrytemplate.python-hosting.com"""
	def get_content(self, req):
		from cherrytemplate import renderTemplate
		self.data['_template_path'] = req['modu.approot'] + '/template/' + self.get_template(req)
		self.data['_renderTemplate'] = renderTemplate
		return eval('_renderTemplate(file=_template_path)', self.data)

class TemplateResource(Resource, TemplateContent):
	pass

class CheetahTemplateResource(Resource, CheetahTemplateContent):
	pass

class ZPTemplateResource(Resource, ZPTemplateContent):
	pass

class CherryTemplateResource(Resource, CherryTemplateContent):
	pass
