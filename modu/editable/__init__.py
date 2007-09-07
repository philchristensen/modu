# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Provides classes for implementing editors for Storable objects.
"""

from zope.interface import Interface

from modu.persist import storable
from modu.util import tags

class IItemdef(Interface):
	pass

class IDatatype(Interface):
	"""
	I can take a field definition from an Editable itemdef and return a form element.
	
	Datatypes can also answer various questions about how that form should be handled.
	"""
	
	def get_form_element(self, style, definition, storable):
		"""
		Take the given definition, and return a FormNode.
		
		The result is prepopulated with data from the provided storable.
		"""
	
	def update_storable(self, req, definition, storable):
		"""
		Can be implemented by IDatatypes that require complex handling of POST data.
		"""
	
	def is_postwrite_field(self):
		"""
		Does this IDatatype write its data as part of the normal save process?
		
		If this function returns True, the items will be ignored during the
		regular process and given a chance to write after the main record has
		been saved.
		"""
