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
		ac_cb_id = '%s-%s-ac-callback' % (form_name, name)
		
		ac_javascript = '$("#%s").autocomplete("%s", '
		ac_javascript += '{onItemSelect:get_ac_callback("%s"), autoFill:1, selectFirst:1, selectOnly:1});'
		ac_javascript = ac_javascript % (ac_id, definition['url'], ac_cb_id)
		ac_javascript = tags.script(type='text/javascript')[ac_javascript]
		
		ac_field = form.FormNode('%s-autocomplete' % name)
		ac_field(type='textfield', weight=0, attributes={'id':ac_id})
		
		js_markup = form.FormNode('%s-sc-js')
		js_markup(type='markup', weight=1, value=ac_javascript)
		
		value_field = form.FormNode(name)
		value_field(type='hidden', weight=2, value=getattr(storable, name, None), attributes={'id':ac_cb_id})
		
		store = storable.get_store()
		
		value = definition['fvalue']
		label = definition['flabel']
		table = definition['ftable']
		
		if(hasattr(storable, name)):
			query = 'SELECT %s FROM %s WHERE %s = %%s' % (label, table, value)
			print query
			results = store.pool.runQuery(query, getattr(storable, name))
			if(results):
				ac_field(value=results[0][label])
			else:
				value_field(value=0)
		
		frm = form.FormNode('%s-ac-fieldset' % name)(type='fieldset', style='brief')
		frm.children[ac_field.name] = ac_field
		frm.children[js_markup.name] = js_markup
		frm.children[value_field.name] = value_field
		
		return frm
	
	