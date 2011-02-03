# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Cheetah Template support code.
"""

import os, os.path, re, threading, stat
import pkg_resources as pkg

cheetah_lock = threading.BoundedSemaphore()
cheetah_template_cache = {}

def render(template, template_type, template_data, **params):
	options = {}
	if(template_type == 'filename'):
		template_root = params['template_root']
		if(isinstance(template_root, tuple)):
			rsrc_file = pkg.resource_stream(template_root[0], os.path.join(template_root[1], template))
			options['file'] = TemplateStream(rsrc_file)
		else:
			template_path = os.path.join(template_root, template)
			module_name = re.sub(r'\W+', '_', template).strip('_')
			
			options['file'] = open(template_path)
	elif(template_type == 'str'):
		template_root = None
		template_path = None
		if('module_name' in params):
			module_name = 'MODU_Dyn_%s' % params['module_name']
		else:
			module_name = None
		
		options['source'] = template
	else:
		raise RuntimeError('unknown template type: %s' % template_type)
	
	if(isinstance(template_root, str)):
		module_root = params.get('compiled_template_root', template_root)
		module_path = os.path.join(module_root, module_name + '.py')
	else:
		module_path = None
	
	# because we have to manage cheetah_template_cache, and moduTemplateDirectoryCallback on the class instance
	cheetah_lock.acquire()
	try:
		def _template_cb(parent_template, template):
			if('template_callback' not in params):
				raise RuntimeError("No 'template_callback' function was passed to modu.web.cheetah.render().")
			if not(callable(params['template_callback'])):
				raise RuntimeError("modu.web.cheetah.render(): 'template_callback' %r is not callable." % params['template_callback'])
			return params['template_callback'](template)
		
		CheetahModuTemplate.moduTemplateDirectoryCallback = _template_cb
	
		try:
			# note that this might raise an exception because
			# template_path is None, but that's okay.
			needs_recompile = (os.stat(template_path).st_mtime > os.stat(module_path).st_mtime)
		except:
			needs_recompile = True
		
		moduleGlobals = {'CHEETAH_dynamicallyAssignedBaseClass_CheetahModuTemplate':CheetahModuTemplate}
		
		# if I can read the template class, and it hasn't been modified
		if(module_path):
			module_readable = os.access(module_path, os.F_OK)
			
			if(needs_recompile):
				if('useStackFrames' in params):
					options['compilerSettings']=dict(useStackFrames=False)
				
				pysrc = CheetahModuTemplate.compile(returnAClass=False,
												moduleName=module_name,
												className=module_name,
												baseclass=CheetahModuTemplate,
												moduleGlobals=moduleGlobals, **options)
				module_file = open(module_path, 'w')
				module_file.write(pysrc)
				module_file.close()
				
				exec pysrc in moduleGlobals
				template_class = moduleGlobals[module_name]
			else:
				if(module_path in cheetah_template_cache):
					template_class = cheetah_template_cache[module_path]
				else:
					#load module and instantiate template
					execfile(module_path, moduleGlobals)
					template_class = moduleGlobals[module_name]
			
			cheetah_template_cache[module_path] = template_class
		# I know I won't be able to write the template class, or this is a string-based template.
		else:
			template_class = CheetahModuTemplate.compile(baseclass=CheetahModuTemplate,
														moduleGlobals=moduleGlobals, **options)
	finally:
		cheetah_lock.release()
	
	result = template_class(searchList=[template_data])
	try:
		return str(result)
	except UnicodeEncodeError, e:
		result = unicode(result)
		return result.encode('utf-8')


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

class TemplateStream(file):
	def __init__(self, f):
		file.__getattribute__(self, '__dict__')['f'] = f
	
	def __getattribute__(self, name):
		return getattr(file.__getattribute__(self, 'f'), name)
	
	def __setattr__(self, name, value):
		return setattr(file.__getattribute__(self, 'f'), name, value)

class CheetahModuTemplate(CheetahTemplate):
	"""
	An adapter class to provide Cheetah Template #include support in modu.
	
	@ivar moduTemplateDirectory: the path to the current template engine's
		template directory.
	@type moduTemplateDirectory: str
	"""
	@classmethod
	def compile(cls, *args, **kwargs):
		if('baseclass' not in kwargs):
			kwargs['baseclass'] = CheetahModuTemplate
		return CheetahTemplate.compile(*args, **kwargs)
	
	def serverSidePath(self, path=None, normpath=os.path.normpath, abspath=os.path.abspath):
		"""
		Return the proper template directory, if set by the user.
		"""
		if(hasattr(self, 'moduTemplateDirectoryCallback')):
			templateDirectory = self.moduTemplateDirectoryCallback(path)
			if(isinstance(templateDirectory, tuple)):
				rsrc_file = pkg.resource_stream(templateDirectory[0], os.path.join(templateDirectory[1], path))
				return TemplateStream(rsrc_file)
			else:
				templatePath = os.path.join(templateDirectory, path)
				return normpath(abspath(templatePath))
		return super(CheetahModuTemplate, self).serverSidePath(path, normpath, abspath)
	
	def _getTemplateAPIClassForIncludeDirectiveCompilation(self, source, file):
		return CheetahModuTemplate
