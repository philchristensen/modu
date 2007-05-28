# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

class Controller(object):
	"""
	This class defines something that reacts when a path is request.
	"""
	def get_paths(self):
		"""
		Return all paths that this controller supports.
		"""
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)
	
	def get_response(self, request):
		"""
		Do whatever this thing should do when a path is loaded.
		"""
		raise NotImplementedError('%s::get_response()' % self.__class__.__name__)

class Content(object):
	"""
	This class represents a piece of content that has a MIME-type of some kind.
	"""
	def prepare_content(self, request):
		"""
		Run any neccessary code that prepares this content object for display.
		This method is only called once.
		"""
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_content(self, request):
		"""
		Return the content for this item. This method can be called multiple times,
		but is always called **after** prepare_content()
		"""
		raise NotImplementedError('%s::get_content()' % self.__class__.__name__)
	
	def get_content_type(self, request):
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
	def get_response(self, request):
		self.prepare_content(request)
		return self.get_content(request)
	
	def get_paths(self):
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)
	
	def prepare_content(self, request):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_content(self, request):
		raise NotImplementedError('%s::get_content()' % self.__class__.__name__)
	
	def get_content_type(self, request):
		raise NotImplementedError('%s::get_content_type()' % self.__class__.__name__)

class TemplateResource(Resource):
	def __init__(self):
		self.data = {}
	
	def add_slot(self, name, value):
		self.data[name] = value
	
	def get_content(self, request):
		import string
		engine = string.Template(self.get_template(request))
		return engine.safe_substitute(self.data)
	
	def get_content_type(self, request):
		return 'text/html'
	
	def get_paths(self):
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)
	
	def prepare_content(self, request):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, request):
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)

class CheetahTemplateResource(TemplateResource):
	"""http://www.cheetahtemplate.org"""
	def get_content(self, request):
		from Cheetah.Template import Template
		template_file = open(request.approot + '/template/' + self.get_template(request))
		self.template = Template(file=template_file, searchList=[self.data])
		return str(self.template)

class ZPTemplateResource(TemplateResource):
	"""http://zpt.sourceforge.net"""
	def get_content(self, request):
		from ZopePageTemplates import PageTemplate
		class ZPTDathomirTemplate(PageTemplate):
			def __call__(self, context={}, *args):
				if not context.has_key('args'):
					context['args'] = args
				return self.pt_render(extra_context=context)
		template_file = open(request.approot + '/template/' + self.get_template(request))
		self.template = ZPTDathomirTemplate()
		self.template.write(template_file.read())
		return self.template(context={'here':self.data})

class CherryTemplateResource(TemplateResource):
	"""http://cherrytemplate.python-hosting.com"""
	def get_content(self, request):
		from cherrytemplate import renderTemplate
		self.data['_template_path'] = request.approot + '/template/' + self.get_template(request)
		self.data['_renderTemplate'] = renderTemplate
		return eval('_renderTemplate(file=_template_path)', self.data)
