# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope import interface
from zope.interface import implements

import os

try:
	import cPickle as pickle
except:
	import pickle

class IResource(interface.Interface):
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


class IResourceDelegate(IResource):
	"""
	Classes that implement this object can emulate a Resource by
	returning some arbitrary Resource object.
	"""
	def get_delegate(self, req):
		"""
		Return a this object's Resource delegate.
		"""

class Resource(object):
	implements(IResource)
	
	def set_content_provider(self, content_provider):
		self.content_provider = content_provider
	
	def get_content_provider(self):
		if(not hasattr(self, 'content_provider') and IContent.providedBy(self)):
			return self
		return self.content_provider
	
	def get_response(self, req):
		cnt = self.get_content_provider()
		if(IAccessControl.providedBy(cnt)):
			cnt.check_access(req)
		
		cnt.prepare_content(req)
		
		req['modu.app'].add_header('Content-Type', cnt.get_content_type(req))
		
		content = cnt.get_content(req)
		
		req['modu.app'].add_header('Content-Length', len(content))
		
		return content
	
	def get_paths(self):
		raise NotImplementedError('%s::get_paths()' % self.__class__.__name__)


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


class ITemplate(interface.Interface):
	"""
	A template implementor has slots and some opaque value that
	represents the template itself.
	"""
	def set_slot(self, key, value):
		"""
		Set a slot in the template to the provided key and value.
		"""
	
	def get_template(self, req):
		"""
		Get an opaque value representing the template. For most template engines
		this is probably a filename, but for the default TemplateContent class, it's
		a StringTemplate-style string.
		"""


class TemplateContent(object):
	implements(IContent, ITemplate)
	
	def __getattr__(self, key):
		if(key == 'data'):
			self.data = {}
			return self.data
		raise AttributeError(key)
	
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
	
	def get_template(self, req):
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)

# According to the docs, Template can take awhile to load.
try:
	from Cheetah.Template import Template as CheetahTemplate
except:
	def CheetahTemplate(*args, **kwargs):
		raise RuntimeError("Cannot find the Cheetah Template modules.")
	
class CheetahTemplateContent(TemplateContent):
	"""http://www.cheetahtemplate.org"""
	def get_content(self, req):
		
		template_path = req['modu.approot'] + '/template/' + self.get_template(req)
		template_file = open(template_path)
		self.template = CheetahTemplate(file=template_file, searchList=[self.data])
		
		return str(self.template)
	
	def prepare_content(self, req):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)


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
	
	def prepare_content(self, req):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)


class CherryTemplateContent(TemplateContent):
	"""http://cherrytemplate.python-hosting.com"""
	def get_content(self, req):
		from cherrytemplate import renderTemplate
		self.data['_template_path'] = req['modu.approot'] + '/template/' + self.get_template(req)
		self.data['_renderTemplate'] = renderTemplate
		return eval('_renderTemplate(file=_template_path)', self.data)
	
	def prepare_content(self, req):
		raise NotImplementedError('%s::prepare_content()' % self.__class__.__name__)
	
	def get_template(self, req):
		raise NotImplementedError('%s::get_template()' % self.__class__.__name__)


class IAccessControl(interface.Interface):
	"""
	An access controlled object can look at a request and determine if
	the user is allowed access or not.
	"""
	def check_access(self, req, throws=True):
		"""
		Is this request allowed access?
		"""


class RoleBasedAccessControl(object):
	implements(IAccessControl)
	
	def check_access(self, req):
		if('modu.user' in req):
			pass
		return False
	
	def get_perms(self, req):
		raise NotImplementedError('%s::get_perms()' % self.__class__.__name__)


class TemplateResource(Resource, TemplateContent):
	pass


class CheetahTemplateResource(Resource, CheetahTemplateContent):
	pass


class ZPTemplateResource(Resource, ZPTemplateContent):
	pass


class CherryTemplateResource(Resource, CherryTemplateContent):
	pass
