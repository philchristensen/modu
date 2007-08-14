# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage selection interfaces (list selects, radio buttons, etc).
"""

from twisted import plugin

from zope.interface import classProvides

from modu.web.editable import IDatatype, Field
from modu.util import form

class SelectField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='select', value=getattr(storable, name, None), options=definition.get('options', {}))
		return frm


