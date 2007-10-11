# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
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

import os, os.path, re, threading, stat, mimetypes

try:
	import cPickle as pickle
except:
	import pickle

from zope import interface
from zope.interface import implements

class IResource(interface.Interface):
	"""
	This class defines something that reacts when a path is requested.
	"""
	def get_paths(self):
		"""
		Return all paths that this controller supports.
		"""
	
	def get_response(self, req):
		"""
		Do whatever this thing should do when a path is loaded.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""


class IResourceDelegate(interface.Interface):
	"""
	Classes that implement this object can emulate a Resource by
	returning some arbitrary Resource object.
	"""
	def get_delegate(self, req):
		"""
		Return a this object's Resource delegate.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""

class IContent(interface.Interface):
	"""
	This class represents a piece of content that has a MIME-type of some kind.
	"""
	def prepare_content(self, req):
		"""
		Run any neccessary code that prepares this content object for display.
		This method is only called once.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
	
	def get_content(self, req):
		"""
		Return the content for this item. This method can be called multiple times,
		but is always called **after** prepare_content()
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		"""
	
	def get_content_type(self, req):
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
	def set_slot(self, key, value):
		"""
		Set a slot in the template to the provided key and value.
		
		@param name: the name of the slot
		@type name: str
		
		@param value: the value to set
		"""
	
	def get_slot(self, key, default=None):
		"""
		Return the value of the slot with the provided key.
		If the item doesn't exist, and default isn't provided, throw an exception.
		
		@param name: the slot to fetch
		@type name: str
		
		@param default: return value if there is no slot by that name
		
		@returns: some value
		"""
	
	def get_slots(self):
		"""
		Return a list of slots added to template.
		
		@returns: a list of slot names
		@rtype: list(str)
		"""
	
	def get_template(self, req):
		"""
		Get an opaque value representing the template. For most template engines
		this is probably a filename, but for the default TemplateContent class, it's
		a StringTemplate-style string.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@returns: some value that makes sense to the template engine
		"""
	
	def get_template_root(self, req, template=None):
		"""
		This function gives an opportunity for template resources to support an
		arbitrary number of template distributions, to allow implementation of themes
		and default templates.
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
		
		@returns: the dirname of the template directory.
		@rtype: str
		"""


class IAccessControl(interface.Interface):
	"""
	An access controlled object can look at a request and determine if
	the user is allowed access or not.
	"""
	def check_access(self, req):
		"""
		Is this request allowed access?
		
		@param req: the current request
		@type req: L{modu.web.app.Request}
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
	
	def get_content_provider(self):
		"""
		Set the IContent implementor that will generate content for this resource.
		
		If there is no content provider set, but the current instance is a IContent
		implementor (because of subclassing/inheritence), this method may return self.
		
		@returns: the object to generate content for this Resource
		@rtype: L{IContent} implementor
		"""
		if(not hasattr(self, 'content_provider') and IContent.providedBy(self)):
			return self
		return self.content_provider
	
	def get_response(self, req):
		"""
		@see: L{IResource.get_response()}
		"""
		cnt = self.get_content_provider()
		if(IAccessControl.providedBy(cnt)):
			cnt.check_access(req)
		
		cnt.prepare_content(req)
		
		req.app.add_header('Content-Type', cnt.get_content_type(req))
		
		content = cnt.get_content(req)
		
		if(isinstance(content, str)):
			req.app.add_header('Content-Length', len(content))
			return [content]
		else:
			return content
	
	def get_paths(self):
		"""
		@see: L{IResource.get_paths()}
		"""
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)


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
			self.set_slot('header_content', "\n".join([str(i) for i in req.content.get('header')]))
		if('modu.user' in req):
			self.set_slot('user', req['modu.user'])
		else:
			self.set_slot('user', None)
	
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
		return os.path.join(req.approot, 'template')


# According to the docs, Template can take awhile to load,
# so it's loaded on startup.
try:
	from Cheetah.Template import Template as CheetahTemplate
except:
	class CheetahTemplate(object):
		"""
		CheetahTemplate substitution class for when Cheetah isn't installed.
		
		This class allows the loading of the Cheetah Template system on
		modu startup.
		"""
		@staticmethod
		def compile(*args, **kwargs):
			"""
			Raise a intelligent error message.
			"""
			raise RuntimeError("Cannot find the Cheetah Template modules.")
		
		def __init__(*args, **kwargs):
			"""
			Raise a intelligent error message.
			"""
			raise RuntimeError("Cannot find the Cheetah Template modules.")

class CheetahModuTemplate(CheetahTemplate):
	"""
	An adapter class to provide Cheetah Template #include support in modu.
	
	@ivar moduTemplateDirectory: the path to the current template engine's
		template directory.
	@type moduTemplateDirectory: str
	"""
	def serverSidePath(self, path=None, normpath=os.path.normpath, abspath=os.path.abspath):
		"""
		Return the proper template directory, if set by the user.
		"""
		if(hasattr(self, 'moduTemplateDirectoryCallback')):
			templatePath = os.path.join(self.moduTemplateDirectoryCallback(path), path)
			return normpath(abspath(templatePath))
		return super(CheetahModuTemplate, self).serverSidePath(path, normpath, abspath)


cheetah_lock = threading.BoundedSemaphore()

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
		
		template = self.get_template(req)
		template_root = self.get_template_root(req)
		template_path = os.path.join(template_root, template)
		
		module_name = re.sub(r'\W+', '_', template)
		module_root = req.app.config.get('compiled_template_root', template_root)
		module_path = os.path.join(module_root, module_name + '.py')
		
		# because we have to manage moduTemplateDirectoryCallback on the class instance
		cheetah_lock.acquire()
		try:
			def _template_cb(parent_template, template):
				return self.get_template_root(req, template)
			
			CheetahModuTemplate.moduTemplateDirectoryCallback = _template_cb
		
			try:
				needs_recompile = (os.stat(template_path).st_mtime > os.stat(module_path).st_mtime)
			except:
				needs_recompile = True
			
			moduleGlobals = {'CHEETAH_dynamicallyAssignedBaseClass_CheetahModuTemplate':CheetahModuTemplate}
		
			# if I can't read the template class, i'll try to create one
			if(os.access(module_path, os.F_OK) and not needs_recompile):
				#load module and instantiate template
				execfile(module_path, moduleGlobals)
				self.template_class = moduleGlobals[module_name]
			# if I know I will be able to save a template class
			elif(needs_recompile and (os.access(module_path, os.W_OK) or not os.access(module_path, os.F_OK))):
				pysrc = CheetahModuTemplate.compile(file=open(template_path),
												returnAClass=False,
												moduleName=module_name,
												className=module_name,
												baseclass=CheetahModuTemplate,
												moduleGlobals=moduleGlobals)
				module_file = open(module_path, 'w')
				module_file.write(pysrc)
				module_file.close()
		
				exec pysrc in moduleGlobals
				self.template_class = moduleGlobals[module_name]
			else:
				self.template_class = CheetahModuTemplate.compile(file=open(template_path),
															baseclass=CheetahModuTemplate,
															moduleGlobals=moduleGlobals)
		finally:
			cheetah_lock.release()
		
		return str(self.template_class(searchList=[self.data]))
	
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


class ZPTemplateContent(TemplateContent):
	"""
	Basic support for the Zope Page Templates library.
	"""
	def get_content(self, req):
		"""
		@see: L{IContent.get_content()}
		"""
		super(ZPTemplateContent, self).get_content(req)
		
		from ZopePageTemplates import PageTemplate
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
		
		from cherrytemplate import renderTemplate
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
	pass


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
