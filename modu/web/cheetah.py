# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Cheetah Template support code.
"""

import os, os.path, re, threading, stat

cheetah_lock = threading.BoundedSemaphore()

def render(template, template_type, template_data, **params):
	options = {}
	if(template_type == 'filename'):
		template_root = params['template_root']
		template_path = os.path.join(template_root, template)
		module_name = re.sub(r'\W+', '_', template)
		
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
	
	if(template_root):
		module_root = params.get('compiled_template_root', template_root)
		module_path = os.path.join(module_root, module_name + '.py')
	else:
		module_path = None
	
	# because we have to manage moduTemplateDirectoryCallback on the class instance
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
	
		# if I can't read the template class, i'll try to create one
		if(module_path and os.access(module_path, os.F_OK) and not needs_recompile):
			#load module and instantiate template
			execfile(module_path, moduleGlobals)
			template_class = moduleGlobals[module_name]
		# if I know I will be able to save a template class
		elif(module_path and needs_recompile and (os.access(module_path, os.W_OK) or not os.access(module_path, os.F_OK))):
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
			template_class = CheetahModuTemplate.compile(baseclass=CheetahModuTemplate,
														moduleGlobals=moduleGlobals, **options)
	finally:
		cheetah_lock.release()
	
	return str(template_class(searchList=[template_data]))


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

