# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
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
	"""
	An itemdef is a special object that defines a form for a database table.
	
	This interface is mostly a tag to detect itemdefs via
	the Twisted plugin system.
	"""
	pass

class IDatatype(Interface):
	"""
	I can take a field definition from an Editable itemdef and return a form element.
	
	Datatypes can also answer various questions about how that form should be handled.
	"""
	
	def get_form_element(style, definition, storable):
		"""
		Take the given definition, and return a FormNode.
		
		The result is prepopulated with data from the provided storable.
		
		@param style: Generate for 'listing', 'search', or 'detail' views.
		@type style: str
		
		@param definition: The definition of the field to generate
		@type definition: L{modu.editable.define.definition}
		
		@param storable: The Storable instance to fill the form data with.
		@type storable: L{modu.persist.storable.Storable} subclass
		
		@return: The generated form
		@rtype: L{modu.util.form.FormNode}
		"""
	
	def update_storable(req, definition, storable):
		"""
		Can be implemented by IDatatypes that require complex handling of POST data.
		
		@param req: The current request
		@type req: L{modu.web.app.Request}
		
		@param definition: The definition of the field
		@type definition: L{modu.editable.define.definition}
		
		@param storable: The Storable instance to update.
		@type storable: L{modu.persist.storable.Storable} subclass
		"""
	
	def is_postwrite_field():
		"""
		Does this IDatatype write its data as part of the normal save process?
		
		@return: if True, the items will be ignored during the
			regular process and given a chance to write after the
			main record has been saved.
		@rtype: bool
		"""
