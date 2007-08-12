# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted import plugin

from zope.interface import classProvides, implements

from modu.web.editable import IDatatype
from modu.util import form

class StringField(object):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_form_element(self, name, style, definition, storable):
		reference_form = form.FormNode(name)
		reference_form(type='textfield', title=definition['title'], value=getattr(storable, name))
		return reference_form