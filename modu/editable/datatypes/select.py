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
	implements(IDatatype)
	
	def get_element(self, style, storable):
		if(style == 'listing' or self.get('read_only', False)):
			return form.FormNode(self.name)(type='label', value=getattr(storable, self.name, None))
		
		frm = form.FormNode(self.name)
		frm(type='select', value=getattr(storable, self.name, None), options=self.get('options', {}))
		return frm


