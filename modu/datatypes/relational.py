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
	
	inherited_attributes = ['size']
	
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
	
	def get_element(self, name, style, definition, storable):
		form_name = '%s-form' % storable.get_table()
		ac_id = '%s-%s-autocomplete' % (form_name, name)
		ac_cb_id = '%s-%s-ac-callback' % (form_name, name)
		
		ac_javascript = '$("#%s").autocomplete("%s", '
		ac_javascript += '{onItemSelect:select_foreign_item("%s"), autoFill:1, selectFirst:1, selectOnly:1, minChars:1});'
		ac_javascript = ac_javascript % (ac_id, definition['url'], ac_cb_id)
		ac_javascript = tags.script(type='text/javascript')[ac_javascript]
		
		ac_field = form.FormNode('%s-autocomplete' % name)
		ac_field(type='textfield', weight=0, attributes={'id':ac_id}, suffix=ac_javascript)
		
		value_field = form.FormNode(name)
		value_field(type='hidden', weight=2, value=getattr(storable, name, None), attributes={'id':ac_cb_id})
		
		store = storable.get_store()
		
		value = definition['fvalue']
		label = definition['flabel']
		table = definition['ftable']
		
		if(hasattr(storable, name)):
			query = 'SELECT %s FROM %s WHERE %s = %%s' % (label, table, value)
			
			results = store.pool.runQuery(query, getattr(storable, name))
			if(results):
				ac_field(value=results[0][label])
			else:
				value_field(value=0)
		
		frm = form.FormNode('%s-ac-fieldset' % name)(type='fieldset', style='brief')
		frm.children[ac_field.name] = ac_field
		frm.children[value_field.name] = value_field
		
		return frm


class ForeignMultipleAutocompleteField(Field):
	classProvides(plugin.IPlugin, IDatatype)
	
	def get_element(self, name, style, d, storable):
		mlabel = d.get('flabel', '')
		if(mlabel.find('.') == -1):
			mlabel = 'm.%s' % mlabel
		mlabel = d.get('flabel_sql', mlabel)
		
		ntom_query = """SELECT m.%s AS value, %s AS label
						FROM %s m
						INNER JOIN %s n2m ON m.%s = n2m.%s AND n2m.%s = %%s
						ORDER BY label""" % (d['fvalue'], mlabel,
										  d['ftable'],
										  d['ntof'], d.get('f_id', 'id'),
										  d['ntof_f_id'], d['ntof_n_id'])
		
		store = storable.get_store()
		results = store.pool.runQuery(ntom_query, storable.get_id())
		options = dict([(str(result['value']), result['label']) for result in results])
		
		form_name = '%s-form' % storable.get_table()
		ac_id = '%s-%s-autocomplete' % (form_name, name)
		select_id = '%s-foreign-select' % name
		
		hidden_options = ''
		for value in options:
			hidden_options += tags.input(type='hidden', name='%s[%s]' % (form_name, name), value=value)
		
		select_frm = form.FormNode('%s-select-view' % name)
		select_frm(type='select', options=options, size=d.get('size', 5),
					multiple=None, suffix=hidden_options + '<br/>', attributes={'id':select_id})
		
		ac_js = '$("#%s").autocomplete("%s", {onItemSelect:add_foreign_item("%s", "%s"), autoFill:1, selectFirst:1, selectOnly:1, minChars:1});' % (ac_id, d['url'], form_name, name)
		ac_controls = tags.script(type='text/javascript')[ac_js]
		
		ac_field = form.FormNode('%s-autocomplete' % name)
		ac_field(type='textfield', weight=10, attributes={'id':ac_id}, suffix=ac_controls)
		
		frm = form.FormNode('%s-ac-fieldset' % name)(type='fieldset', style='brief')
		frm.children[select_frm.name] = select_frm
		frm.children[ac_field.name] = ac_field
		
		return frm
	
	def update_storable(self, name, req, form, d, storable):
		form_data = form.data[form.name]
		store = storable.get_store()
		item_id = storable.get_id()
		
		delete_query = persist.build_delete(d['ntof'], {d['ntof_n_id']:item_id})
		store.pool.runOperation(delete_query)
		
		print form.data
		if(name in form_data):
			values = form_data[name].value
			if not(isinstance(values, list)):
				values = [values]
			data = [{d['ntof_n_id']:item_id, d['ntof_f_id']:val} for val in values]
			insert_query = persist.build_insert(d['ntof'], data)
			store.pool.runOperation(insert_query)
		elif(d.get('required', False)):
			# A conundrum...
			# It's got to be a postwrite field, because a new record would
			# have to be saved before we could insert a record elsewhere with
			# a foreign key (supposing for a minute we weren't use MySQL, argh)
			#
			# This means that it's impossible for this field to stop the writing
			# of the record at this point, thus 'required' is currently meaningless.
			#
			# Should there be a way for a postwrite field to validate separately,
			# before the write?
			#
			# I think the way it was supposed to work in Procuro was that if you
			# are using GUIDs, you can fill the field at creation time, otherwise
			# you saw a field that told you to save before editing (lame).
			return False
		return True
	
	def is_postwrite_field(self):
		return True