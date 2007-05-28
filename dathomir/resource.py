# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

class Controller(object):
	def get_paths(self):
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)
	
	def get_response(self, request):
		raise NotImplementedError('%s::get_response()' % self.__class__.__name__)

class Content(object):
	def prepare_content(self, request):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_content(self, request):
		raise NotImplementedError('%s::get_content()' % self.__class__.__name__)
	
	def get_content_type(self, request):
		raise NotImplementedError('%s::get_content_type()' % self.__class__.__name__)

class Resource(Controller, Content):
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
	def get_content(self, request):
		from Cheetah.Template import Template
		template_file = open(request.approot + '/template/' + self.get_template(request))
		self.template = Template(file=template_file, searchList=[self.data])
		return str(self.template)

class ZPTemplateResource(TemplateResource):
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
