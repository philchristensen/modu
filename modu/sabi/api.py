# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from zope import interface

def invoke(func, *args, **kwargs):
	"""
	Iterate through all the (registered) extensions and
	call the function on each one, passing the same
	args and kwargs each time.
	"""
	pass

class IExtension(interface.Interface):
	def initialize(self, req, app):
		"""
		Called when first configuring an application
		in this memory space. Allows creation of app
		"services" that can be stored in the req object.
		"""
	
	def menu(self, req, tree, will_cache=False):
		"""
		Called when first using an application in this
		memory space. If will_cache is true, the result
		of this function will be cached.
		"""
	
	def form_alter(self, req, form_id, form):
		"""
		Before a form is rendered, any available plugins can
		use this hook to modify that form.
		"""
	
	def provided_factories(self):
		"""
		Returns an array of short names to define the objects
		this extension can create.
		"""
