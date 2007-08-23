# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage boolean-type fields.
"""

from zope.interface import implements

from modu.editable import IDatatype, define
from modu.util import form
from modu import persist

class CheckboxField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		frm = form.FormNode(self.name)
		frm(type='checkbox', value=self.get('value', 1))
		if(getattr(storable, self.name, None) == self.get('value', 1)):
			frm(checked=True)
		
		if(style == 'listing' or self.get('read_only', False)):
			frm(disabled=True)
		
		return frm

