# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
Fundamental modu building-blocks.

Resources are activated on the L{modu.web.app.Application} object and are
placed inside the application URLNode tree.

The modu concept of a Resource is in practice more of an organizational tool
than a rigid separation of responsibility. A resource can serve any URL under
it's root path, and use any number of methods for returning content.

Use of templating engines is fairly fundamental to the modu framework, however,
and the Cheetah template system is the preferred engine, although limited support
is available for CherryTemplate and ZPT templates.

@see: modu.util.url.URLNode
"""

import os.path

from zope import interface
from zope.interface import implements

from modu.web import HTTPStatus, cheetah

class IResource(interface.Interface):
	"""
	This class defines something that reacts when a path is requested.
	"""
	def get_response(req):
		"""
		Do whatever this thing should do when a path is loaded.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
	
	def get_content_provider(req):
		"""
		Set the IContent implementor that will generate content for this resource.
		
		If there is no content provider set, but the current instance is a IContent
		implementor (because of subclassing/inheritence), this method may return self.
		
		@returns: the object to generate content for this Resource
		@rtype: L{IContent} implementor
		"""

class IResourceDelegate(interface.Interface):
	"""
	Classes that implement this object can emulate a Resource by
	returning some arbitrary Resource object.
	"""
	def get_delegate(req):
		"""
		Return a this object's Resource delegate.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""

class IContent(interface.Interface):
	"""
	This class represents a piece of content that has a MIME-type of some kind.
	"""
	def prepare_content(req):
		"""
		Run any neccessary code that prepares this content object for display.
		This method is only called once.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
	
	def get_content(req):
		"""
		Return the content for this item. This method can be called multiple times,
		but is always called **after** prepare_content()
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
	
	def get_content_type(req):
		"""
		Return the mime type of this content.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""


class ITemplate(interface.Interface):
	"""
	A template implementor has slots and some opaque value that
	represents the template itself.
	"""
	def set_slot(key, value):
		"""
		Set a slot in the template to the provided key and value.
		
		@param name: the name of the slot
		@type name: str
		
		@param value: the value to set
		"""
	
	def get_slot(key, default=None):
		"""
		Return the value of the slot with the provided key.
		If the item doesn't exist, and default isn't provided, throw an exception.
		
		@param name: the slot to fetch
		@type name: str
		
		@param default: return value if there is no slot by that name
		
		@returns: some value
		"""
	
	def get_slots():
		"""
		Return a list of slots added to template.
		
		@returns: a list of slot names
		@rtype: list(str)
		"""
	
	def get_template(req):
		"""
		Get an opaque value representing the template. For most template engines
		this is probably a filename, but for the default TemplateContent class, it's
		a StringTemplate-style string.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@returns: some value that makes sense to the template engine
		"""
	
	def get_template_root(req, template=None):
		"""
		This function gives an opportunity for template resources to support an
		arbitrary number of template distributions, to allow implementation of themes
		and default templates.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@returns: the dirname of the template directory.
		@rtype: str
		"""
	
	def get_template_type():
		"""
		Template resources by default return a filename from get_template(). To
		return the template as a string, this function must be overriden to
		return 'str' instead of the default 'filename'.
		
		@returns: the type of the get_template() return value ('filename', or 'str').
		@rtype: str
		"""


class Resource(object):
	"""
	An abstract HTTP resource.
	
	Resources can act as Controllers in the MVC approach, and supply
	an IContent implementor to generate content.
	
	Direct subclasses of this class can also inherit from an IContent
	implementor, which is the approach taken by the various *TemplateResource
	classes.
	
	@see: L{IResource}
	
	@ivar content_provider: if not None, this object will generate content for this Resource
	@type content_provider: L{IContent} implementor
	"""
	
	implements(IResource)
	
	def set_content_provider(self, content_provider):
		"""
		Set the content provider for this resource.
		
		@param content_provider: if not None, this object will generate content for this Resource
		@type content_provider: L{IContent} implementor
		"""
		if not(IContent.providedBy(content_provider)):
			raise ValueError('%r is not an implementation of IContent.' % content_provider)
		self.content_provider = content_provider
	
	def get_content_provider(self, req):
		"""
		@see: L{IResource.get_content_provider()}
		"""
		if(not hasattr(self, 'content_provider') and IContent.providedBy(self)):
			return self
		return self.content_provider
	
	def get_response(self, req):
		"""
		@see: L{IResource.get_response()}
		"""
		cnt = self.get_content_provider(req)
		
		cnt.prepare_content(req)
		
		req.add_header('Content-Type', cnt.get_content_type(req))
		
		content = cnt.get_content(req)
		
		if(isinstance(content, str)):
			req.add_header('Content-Length', len(content))
			return [content]
		else:
			return content


class WSGIPassthroughResource(Resource):
	implements(IContent)
	
	def __init__(self, wsgi_app):
		self.wsgi_app = wsgi_app
		self.status = '200 OK'
		self.content = []
	
	def prepare_content(self, req):
		def _write(msg):
			self.content.extend(list(msg))
		def _start_response(status, headers, exc_info=None):
			if exc_info is not None:
				try:
					raise exc_info[0], exc_info[1], exc_info[2]
				finally:
					exc_info = None
			self.status = status
			for k, v in headers:
				req.add_header(k, v)
			return _write
		self.content.extend(self.wsgi_app(req, _start_response))
	
	def get_content(self, req):
		raise HTTPStatus(self.status, req.get_headers(), self.content)
	
	def get_content_type(self, req):
		if(req.has_header('Content-Type')):
			return req.get_header('Content-Type')[0]
		return 'text/html'


class TemplateContent(object):
	"""
	Abstract class that handles basic templating functionality.
	
	@ivar data: a template slot to value mapping
	@type data: dict
	"""
	implements(IContent, ITemplate)
	
	def __getattr__(self, key):
		"""
		Convenience hook to create data member variable on demand.
		
		This lets subclasses define their own constructor without having to
		worry about calling the superclass constructor.
		
		@param key: the name of the attribute to fetch
		@type key: str
		
		@returns: some value
		"""
		if(key == 'data'):
			self.data = {}
			return self.data
		raise AttributeError(key)
	
	def set_slot(self, name, value):
		"""
		Set a template varable slot to the provided value.
		
		@see: L{ITemplate.set_slot()}
		
		@param name: the name of the slot
		@type name: str
		
		@param value: the value to set
		"""
		self.data[name] = value
	
	def get_slot(self, name, default=None):
		"""
		Get a value out of the template data.
		
		@see: L{ITemplate.get_slot()}
		
		@param name: the slot to fetch
		@type name: str
		
		@param default: return value if there is no slot by that name
		
		@returns: some value
		"""
		if(name not in self.data):
			if(default is not None):
				return default
			raise KeyError(name)
		return self.data[name]
	
	def get_slots(self):
		"""
		Return a list of slots added to template.
		
		@see: L{ITemplate.get_slots()}
		
		@returns: a list of slot names
		@rtype: list(str)
		"""
		return self.data.keys()
	
	def get_content(self, req):
		"""
		Return the template-generated content.
		
		Subclasses intending to implement new template engine support should
		make sure to call this function if they wish to use the default template
		variable set.
		
		@see: L{IContent.get_content()}
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
		self.set_slot('base_path', req.get_path())
		self.set_slot('req', req)
		if('modu.content' in req):
			def header_content():
				return "\n".join([str(i) for i in req.content.get('header')])
			
			self.set_slot('header_content', header_content)
		if(req.get('modu.user', None) is None):
			self.set_slot('user', None)
		else:
			self.set_slot('user', req['modu.user'])
	
	def get_content_type(self, req):
		"""
		@see: L{IContent.get_content()}
		"""
		return 'text/html'
	
	def prepare_content(self, req):
		"""
		@see: L{IContent.prepare_content()}
		"""
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		"""
		@see: L{IContent.get_template()}
		"""
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)
	
	def get_template_root(self, req, template=None):
		"""
		@see: L{IContent.get_template_root()}
		"""
		if(hasattr(self, 'template_dir')):
			template_root = self.template_dir
		else:
			template_root = getattr(req.app, 'template_dir')
		return template_root
	
	def get_template_type(self):
		"""
		@see: L{IContent.get_template_root()}
		"""
		return 'filename'


class CheetahTemplateContent(TemplateContent):
	"""
	Implement support for the Cheetah Template library.
	
	Although modu allows use of other templating systems on a per-resource basis,
	Cheetah is the primary area of support. Add-on modules distributed with modu
	also require Cheetah for use.
	
	Usage of Cheetah in modu is meant to be somewhat similar to Smarty used in
	modu's PHP predecessor.
	"""
	def get_content(self, req):
		"""
		@see: L{IContent.get_content()}
		"""
		super(CheetahTemplateContent, self).get_content(req)
		kwargs = {}
		compiled_template_root = req.app.config.get('compiled_template_root', None)
		if(compiled_template_root):
			kwargs['compiled_template_root'] = compiled_template_root
		
		if(req.app.config.get('cheetah_useStackFrames')):
			kwargs['useStackFrames'] = req.app.useStackFrames
		
		def _template_callback(template):
			return self.get_template_root(req, template)
		
		return cheetah.render(self.get_template(req), self.get_template_type(), self.data,
								template_root=self.get_template_root(req),
								module_name=self.__class__.__name__,
								template_callback=_template_callback,
								**kwargs)
	
	def prepare_content(self, req):
		"""
		@see: L{IContent.prepare_content()}
		"""
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		"""
		@see: L{ITemplate.get_template()}
		"""
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)
	
	def get_template_type(self):
		"""
		@see: L{ITemplate.get_template_type()}
		"""
		return 'filename'

class ZPTemplateContent(TemplateContent):
	"""
	Basic support for the Zope Page Templates library.
	"""
	def get_content(self, req):
		"""
		@see: L{IContent.get_content()}
		"""
		super(ZPTemplateContent, self).get_content(req)
		try:
			from ZopePageTemplates import PageTemplate
		except:
			from modu.web import app
			app.raise500("The ZopePageTemplates package is missing.")
		class ZPTmoduTemplate(PageTemplate):
			def __call__(self, context={}, *args):
				if not context.has_key('args'):
					context['args'] = args
				return self.pt_render(extra_context=context)
		template_file = open(os.path.join(self.get_template_root(req), self.get_template(req)))
		self.template = ZPTmoduTemplate()
		self.template.write(template_file.read())
		return self.template(context={'here':self.data})
	
	def prepare_content(self, req):
		"""
		@see: L{IContent.prepare_content()}
		"""
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		"""
		@see: L{ITemplate.get_template()}
		"""
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)


class CherryTemplateContent(TemplateContent):
	"""
	Basic support for the CherryTemplate library.
	"""
	def get_content(self, req):
		"""
		@see: L{IContent.get_content()}
		"""
		super(CherryTemplateContent, self).get_content(req)
		
		try:
			from cherrytemplate import renderTemplate
		except:
			from modu.web import app
			app.raise500("The cherrytemplate package is missing.")
		self.data['_template_path'] = os.path.join(self.get_template_root(req), self.get_template(req))
		self.data['_renderTemplate'] = renderTemplate
		return eval('_renderTemplate(file=_template_path)', self.data)
	
	def prepare_content(self, req):
		"""
		@see: L{IContent.prepare_content()}
		"""
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		"""
		@see: L{ITemplate.get_template()}
		"""
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)

class CheetahTemplateResource(Resource, CheetahTemplateContent):
	"""
	A convenience class so further subclasses don't need to think about multiple inheritance ;-).
	"""
	def __init__(self, template=None, template_type='filename'):
		self.__template = template
		self.__template_type = template_type

	def prepare_content(self, req):
		"""
		@see: L{IContent.prepare_content()}
		"""
		if(self.__template):
			return
		else:
			raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		"""
		@see: L{ITemplate.get_template()}
		"""
		if(getattr(self, '__template', None)):
			return self.__template
		else:
			raise NotImplementedError('%s::get_template()' % self.__class__.__name__)
	
	def get_template_type(self):
		"""
		@see: L{ITemplate.get_template_type()}
		"""
		return getattr(self, '__template_type', 'filename')

class ZPTemplateResource(Resource, ZPTemplateContent):
	"""
	A convenience class so further subclasses don't need to think about multiple inheritance ;-).
	"""
	pass

class CherryTemplateResource(Resource, CherryTemplateContent):
	"""
	A convenience class so further subclasses don't need to think about multiple inheritance ;-).
	"""
	pass
