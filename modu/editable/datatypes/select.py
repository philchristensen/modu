# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage selection interfaces (list selects, radio buttons, etc).
"""

from zope.interface import implements

from modu.editable import IDatatype, define
from modu.util import form

class SelectField(define.definition):
	"""
	Allow selection of a value from a list of options.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		if(style == 'listing' or self.get('read_only', False)):
			return form.FormNode(self.name)(type='label', value=getattr(storable, self.get_column_name(), None))
		
		frm = form.FormNode(self.name)
		frm(type=self.get('style', 'select'), value=getattr(storable, self.get_column_name(), None), options=self.get('options', {}))
		return frm


