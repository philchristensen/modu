# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

class Controller(object):
	"""
	This class defines something that reacts when a path is req.
	"""
	def get_paths(self):
		"""
		Return all paths that this controller supports.
		"""
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)
	
	def get_response(self, req):
		"""
		Do whatever this thing should do when a path is loaded.
		"""
		raise NotImplementedError('%s::get_response()' % self.__class__.__name__)

class Content(object):
	"""
	This class represents a piece of content that has a MIME-type of some kind.
	"""
	def prepare_content(self, req):
		"""
		Run any neccessary code that prepares this content object for display.
		This method is only called once.
		"""
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_content(self, req):
		"""
		Return the content for this item. This method can be called multiple times,
		but is always called **after** prepare_content()
		"""
		raise NotImplementedError('%s::get_content()' % self.__class__.__name__)
	
	def get_content_type(self, req):
		"""
		Return the mime type of this content.
		"""
		raise NotImplementedError('%s::get_content_type()' % self.__class__.__name__)

class Resource(Controller, Content):
	"""
	A resource is a combination Controller-Content object that returns its
	content as the result of a request on a particular URL. One should take
	care if using this class directly; since it breaks the MVC relationship
	(in a sense), it should only be directly subclassed when Views are
	implemented by template engines, or when no View is required.
	"""
	def get_response(self, req):
		self.prepare_content(req)
		return self.get_content(req)
	
	def get_paths(self):
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)
	
	def prepare_content(self, req):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_content(self, req):
		raise NotImplementedError('%s::get_content()' % self.__class__.__name__)
	
	def get_content_type(self, req):
		raise NotImplementedError('%s::get_content_type()' % self.__class__.__name__)

class TemplateContent(Content):
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
	
	def prepare_content(self, req):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)

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

class CheetahTemplateResource(Resource, CheetahTemplateContent):
	"""http://www.cheetahtemplate.org"""
	def get_content(self, req):
		from Cheetah.Template import Template
		template_file = open(req['modu.approot'] + '/template/' + self.get_template(req))
		self.template = Template(file=template_file, searchList=[self.data])
		return str(self.template)

class ZPTemplateResource(Resource, ZPTemplateContent):
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

class CherryTemplateResource(Resource, CherryTemplateContent):
	"""http://cherrytemplate.python-hosting.com"""
	def get_content(self, req):
		from cherrytemplate import renderTemplate
		self.data['_template_path'] = req['modu.approot'] + '/template/' + self.get_template(req)
		self.data['_renderTemplate'] = renderTemplate
		return eval('_renderTemplate(file=_template_path)', self.data)
