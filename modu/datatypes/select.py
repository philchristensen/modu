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

class SelectField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		frm = form.FormNode(name)
		frm(type='select', label=definition['label'], value=getattr(storable, name),
			options=definition.get('options', []))
		return frm

class ForeignSelectField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		store = storable.get_store()
		
		value = definition['fvalue']
		label = definition['flabel']
		table = definition['ftable']
		
		results = store.pool.runQuery('SELECT %s, %s FROM %s' % (value, label, table))
		
		options = dict([(item[value], item[label]) for item in results])
		
		frm = form.FormNode(name)
		frm(type='select', label=definition['label'], value=getattr(storable, name), options=options)
		return frm
