# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage foreign key relationships.
"""

from twisted import plugin

from zope.interface import classProvides

from modu.web.editable import IDatatype, Field
from modu.util import form, tags
from modu import persist

class ForeignLabelField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, definition, storable):
		store = storable.get_store()
		
		value = definition['fvalue']
		label = definition['flabel']
		table = definition['ftable']
		
		foreign_label_query = "SELECT %s, %s FROM %s WHERE %s = %%s" % (value, label, table, value)
		foreign_label_query = persist.interp(foreign_label_query, [getattr(storable, name, None)])
		
		results = store.pool.runQuery(foreign_label_query)
		frm = form.FormNode(name)
		frm(type='label')
		
		if(results):
			frm(value=results[0][label])
		
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
		frm(type='select', value=getattr(storable, name, None), options=options)
		return frm


class ForeignAutocompleteField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	inherited_attributes = ['size', 'maxlength']
	
	def get_element(self, name, style, definition, storable):
		form_name = '%s-form' % storable.get_table()
		ac_id = '%s-%s-autocomplete' % (form_name, name)
		ac_javascript = '$("#%s").autocomplete("%s");' % (ac_id, definition['url'])
		ac_support = tags.script(type='text/javascript')[ac_javascript]
		frm = form.FormNode(name)
		frm(type='textfield', value=getattr(storable, name, None),
			suffix=ac_support, attributes={'id':ac_id})
		return frm

	