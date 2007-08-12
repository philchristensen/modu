# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted import plugin

from zope.interface import classProvides, implements

from modu import editable

class StringField(object):
	classProvides(plugin.IPlugin, editable.IDatatype)
	
	def get_form_element(name, style, definition, storable):
		reference_form = form.FormNode(name)
		reference_form(type='textfield', title=definition['title'], value=getattr(storable, name))
		return reference_form