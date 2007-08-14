# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted import plugin

from zope.interface import classProvides

from modu.web.editable import IDatatype, Field
from modu.util import form
from modu import persist

class CheckboxField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='checkbox', value=definition.get('value', 1))
		if(getattr(storable, name, None) == definition.get('value', 1)):
			frm(checked=True)
		return frm

