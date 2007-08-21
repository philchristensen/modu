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
	I can take a field definition from an Editable itemdef and return a form object.
	Datatypes can also answer various questions about how that form should be handled.
	"""
	
	def get_form_element(self, style, definition, storable):
		"""
		Take the given definition, and return a FormNode populated
		with data from the provided storable.
		"""
	
	def update_storable(self, req, definition, storable):
		"""
		The fields of this storable will already be populated in
		most scenarios, but this function can be implemented by
		datatypes who wish to calculate a value based on
		more complex POST data.
		"""
	
	def is_postwrite_field(self):
		"""
		Some fields (particularly file uploads) may need to write their
		data after all other "standard" data has been written. For example,
		they may require the Storable id. If this function returns True,
		the items will be ignored during the regular process and given a
		chance to write after the main record has been saved.
		"""
