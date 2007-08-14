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

class LabelField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='label', value=getattr(storable, name))
		return frm


class DateField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='label', value=getattr(storable, name))
		return frm


class StringField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	inherited_attributes = ['size', 'maxlength']
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(value=getattr(storable, name))
		if(style == 'list'):
			frm(type='label')
		else:
			frm(type='textfield')
		return frm


class TextAreaField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	inherited_attributes = ['rows', 'cols']
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='textarea', value=getattr(storable, name))
		return frm


class PasswordField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(value=getattr(storable, name))
		if(style == 'list'):
			frm(type='label', value='********')
		else:
			frm(type='password')
		return frm