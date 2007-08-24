# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage foreign key relationships.
"""

from zope.interface import implements

from modu.editable import IDatatype, define
from modu.util import form, tags
from modu import persist

class ForeignLabelField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		store = storable.get_store()
		
		value = self['fvalue']
		label = self['flabel']
		table = self['ftable']
		
		foreign_label_query = "SELECT %s, %s FROM %s WHERE %s = %%s" % (value, label, table, value)
		foreign_label_query = persist.interp(foreign_label_query, [getattr(storable, self.name, None)])
		
		results = store.pool.runQuery(foreign_label_query)
		frm = form.FormNode(self.name)
		frm(type='label')
		
		if(results):
			frm(value=results[0][label])
		
		return frm


class ForeignSelectField(define.definition):
	implements(IDatatype)
	
	inherited_attributes = ['size']
	
	def get_element(self, style, storable):
		store = storable.get_store()
		
		value = self['fvalue']
		label = self['flabel']
		table = self['ftable']
		where = self.get('fwhere', '')
		
		if(callable(where)):
			where = where(storable)
		elif(isinstance(where, dict)):
			where = persist.build_where(where)
		
		foreign_query = 'SELECT %s, %s FROM %s ' % (value, label, table)
		if(where):
			foreign_query += where
		
		results = store.pool.runQuery(foreign_query)
		
		options = dict([(item[value], item[label]) for item in results])
		
		frm = form.FormNode(self.name)
		if(style == 'listing' or self.get('read_only', False)):
			foreign_value = getattr(storable, self.name, None)
			frm(type='label', value=options[foreign_value])
		else:
			frm(type='select', value=getattr(storable, self.name, None), options=options)

		return frm


class ForeignAutocompleteField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		form_name = '%s-form' % storable.get_table()
		ac_id = '%s-%s-autocomplete' % (form_name, self.name)
		ac_cb_id = '%s-%s-ac-callback' % (form_name, self.name)
		
		prefs = 'autoFill:1, selectFirst:1, selectOnly:1, minChars:%d, maxItemsToShow:%d' % (self.get('min_chars', 3), self.get('max_choices', 10))
		ac_javascript = '$("#%s").autocomplete("%s", '
		ac_javascript += '{onItemSelect:select_foreign_item("%s"), %s});'
		ac_javascript = ac_javascript % (ac_id, self['url'], ac_cb_id, prefs)
		ac_javascript = tags.script(type='text/javascript')[ac_javascript]
		
		ac_field = form.FormNode('%s-autocomplete' % self.name)
		ac_field(type='textfield', weight=0, attributes={'id':ac_id}, suffix=ac_javascript)
		
		value_field = form.FormNode(self.name)
		value_field(type='hidden', weight=2, value=getattr(storable, self.name, None), attributes={'id':ac_cb_id})
		
		store = storable.get_store()
		
		value = self['fvalue']
		label = self['flabel']
		table = self['ftable']
		
		if(hasattr(storable, self.name)):
			query = 'SELECT %s FROM %s WHERE %s = %%s' % (label, table, value)
			
			results = store.pool.runQuery(query, getattr(storable, self.name))
			if(results):
				ac_field(value=results[0][label])
			else:
				value_field(value=0)
		
		if(style == 'listing' or self.get('read_only', False)):
			return form.FormNode(self.name)(type='label', value=ac_field.attribs('value', ''))
		
		frm = form.FormNode('%s-ac-fieldset' % self.name)(type='fieldset', style='brief')
		frm.children[ac_field.name] = ac_field
		frm.children[value_field.name] = value_field
		
		return frm


class ForeignMultipleAutocompleteField(define.definition):
	implements(IDatatype)
	
	def get_element(self, style, storable):
		mlabel = self.get('flabel', '')
		if(mlabel.find('.') == -1):
			mlabel = 'm.%s' % mlabel
		mlabel = self.get('flabel_sql', mlabel)
		
		where = self.get('fwhere', '')
		
		if(callable(where)):
			where = where(storable)
		elif(isinstance(where, dict)):
			where = persist.build_where(where)
		
		limit = 'LIMIT %d' % self.get('limit_choices', 20)
		
		ntom_query = """SELECT m.%s AS value, %s AS label
						FROM %s m
						INNER JOIN %s n2m ON m.%s = n2m.%s AND n2m.%s = %%s
						%s
						ORDER BY label
						%s""" % (self['fvalue'], mlabel,
										  self['ftable'],
										  self['ntof'], self.get('f_id', 'id'),
										  self['ntof_f_id'], self['ntof_n_id'],
										  where, limit)
		
		store = storable.get_store()
		results = store.pool.runQuery(ntom_query, storable.get_id())
		
		if(style == 'listing' or self.get('read_only', False)):
			label_value = ', '.join([result['label'] for result in results])
			return form.FormNode(self.name)(type='label', value=label_value)
		
		options = dict([(str(result['value']), result['label']) for result in results])
		
		form_name = '%s-form' % storable.get_table()
		ac_id = '%s-%s-autocomplete' % (form_name, self.name)
		select_id = '%s-foreign-select' % self.name
		
		hidden_options = ''
		for value in options:
			hidden_options += tags.input(type='hidden', name='%s[%s]' % (form_name, self.name), value=value)
		
		select_frm = form.FormNode('%s-select-view' % self.name)
		select_frm(type='select', options=options, size=self.get('size', 5),
					multiple=None, suffix=hidden_options + '<br/>', attributes={'id':select_id})
		
		prefs = 'autoFill:1, selectFirst:1, selectOnly:1, minChars:%d, maxItemsToShow:%d' % (self.get('min_chars', 3), self.get('max_choices', 10))
		ac_js = '$("#%s").autocomplete("%s", {onItemSelect:add_foreign_item("%s", "%s"), %s});' % (ac_id, self['url'], form_name, self.name, prefs)
		ac_controls = tags.script(type='text/javascript')[ac_js]
		
		ac_field = form.FormNode('%s-autocomplete' % self.name)
		ac_field(type='textfield', weight=10, attributes={'id':ac_id}, suffix=ac_controls)
		
		frm = form.FormNode('%s-ac-fieldset' % self.name)(type='fieldset', style='brief')
		frm.children[select_frm.name] = select_frm
		frm.children[ac_field.name] = ac_field
		
		return frm
	
	def update_storable(self, req, form, storable):
		form_data = form.data[form.name]
		store = storable.get_store()
		item_id = storable.get_id()
		
		delete_query = persist.build_delete(d['ntof'], {self['ntof_n_id']:item_id})
		store.pool.runOperation(delete_query)
		
		print form.data
		if(name in form_data):
			values = form_data[name].value
			if not(isinstance(values, list)):
				values = [values]
			data = [{self['ntof_n_id']:item_id, self['ntof_f_id']:val} for val in values]
			insert_query = persist.build_insert(self['ntof'], data)
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