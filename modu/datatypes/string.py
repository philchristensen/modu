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

class LabelField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='label', label=definition['label'], value=getattr(storable, name))
		return frm


class StringField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(label=definition['label'], value=getattr(storable, name))
		if(style == 'list'):
			frm(type='label')
		else:
			frm(type='textfield')
		return frm


class PasswordField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(label=definition['label'], value=getattr(storable, name))
		if(style == 'list'):
			frm(type='markup', value='********')
		else:
			frm(type='password')
		return frm