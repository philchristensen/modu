# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Datatypes to manage foreign key relationships.
"""

import time

from zope.interface import implements

from modu.editable import IDatatype, define
from modu.util import form, tags, OrderedDict
from modu.persist import sql

from modu.persist.sql import escape_dot_syntax as q

class ForeignLabelField(define.definition):
	"""
	Display a value from a foreign table based on this field's value.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		store = storable.get_store()
		
		value = self['fvalue']
		label = self['flabel']
		table = self['ftable']
		
		where = self.get('fwhere', 'WHERE %s = %%s' % q(value))
		args = [getattr(storable, self.get_column_name(), None)]
		
		if(callable(where)):
			where = where(storable)
			args = []
		if(isinstance(where, dict)):
			where = sql.build_where(where)
			args = []
		
		foreign_label_query = "SELECT %s, %s FROM %s %s" % (q(value), q(label), q(table), where)
		foreign_label_query = sql.interp(foreign_label_query, args)
		
		results = store.pool.runQuery(foreign_label_query)
		frm = form.FormNode(self.name)
		frm(type='label')
		
		if(results):
			frm(value=results[0][label])
		
		return frm


class ForeignSelectField(define.definition):
	"""
	Allow selection of a foreign value.
	"""
	implements(IDatatype)
	
	inherited_attributes = ['size']
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		store = storable.get_store()
		
		value = self['fvalue']
		label = self['flabel']
		table = self['ftable']
		where = self.get('fwhere', '')
		order_by = self.get('order_by', None)
		
		if(callable(where)):
			where = where(storable)
		if(isinstance(where, dict)):
			where = sql.build_where(where)
		
		foreign_query = 'SELECT %s, %s FROM %s ' % (q(value), q(label), q(table))
		if(where):
			foreign_query += where
		if(order_by):
			foreign_query += 'ORDER BY %s' % order_by
		
		results = store.pool.runQuery(foreign_query)
		
		options = OrderedDict([(item[value], item[label]) for item in results])
		
		frm = form.FormNode(self.name)
		if(style == 'listing' or self.get('read_only', False)):
			foreign_value = getattr(storable, self.get_column_name(), None)
			if(foreign_value in options):
				frm(type='label', value=options[foreign_value])
			else:
				frm(type='label', value='')
		else:
			frm(type='select', value=getattr(storable, self.get_column_name(), None), options=options)

		return frm


class ForeignAutocompleteField(define.definition):
	"""
	Allow selection of a foreign value by autocomplete field.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		form_name = '%s-form' % storable.get_table()
		ac_id = '%s-%s-autocomplete' % (form_name, self.name)
		ac_cb_id = '%s-%s-ac-callback' % (form_name, self.name)
		ac_url = req.get_path(req.prepath, 'autocomplete', storable.get_table(), self.name)
		
		prefs = 'autoFill:1, selectFirst:1, matchSubset:0, selectOnly:1, extraParams:{t:%d}, minChars:%d' % (int(time.time()), self.get('min_chars', 3))
		ac_javascript = '$("#%s").autocomplete("%s", '
		ac_javascript += '{onItemSelect:select_foreign_item("%s"), %s});'
		ac_javascript = ac_javascript % (ac_id, ac_url, ac_cb_id, prefs)
		ac_javascript = tags.script(type='text/javascript')[ac_javascript]
		
		ac_field = form.FormNode('%s-autocomplete' % self.name)
		ac_field(type='textfield', weight=0, attributes={'id':ac_id}, suffix=ac_javascript)
		
		value_field = form.FormNode(self.name)
		value_field(type='hidden', weight=2, value=getattr(storable, self.get_column_name(), None), attributes={'id':ac_cb_id})
		
		store = storable.get_store()
		
		value = self['fvalue']
		label = self['flabel']
		table = self['ftable']
		
		if(hasattr(storable, self.get_column_name())):
			query = 'SELECT %s FROM %s WHERE %s = %%s' % (q(label), q(table), q(value))
			
			field_value = getattr(storable, self.get_column_name())
			if(field_value is not None):
				results = store.pool.runQuery(query, field_value)
				if(results):
					ac_field(value=results[0][label])
				else:
					value_field(value=0)
			else:
				value_field(value=0)
		
		if(style == 'listing' or self.get('read_only', False)):
			return form.FormNode(self.name)(type='label', value=ac_field.attr('value', ''))
		
		req.content.report('header', tags.style(type="text/css")[
			"""@import '%s';""" % req.get_path('/assets/jquery/jquery.autocomplete.css')])
		
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/jquery/jquery-1.2.1.js"))[''])
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/jquery/jquery.autocomplete.js"))[''])
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/editable-autocomplete.js"))[''])
		
		frm = form.FormNode('%s-ac-fieldset' % self.name)(type='fieldset', style='brief')
		frm[ac_field.name] = ac_field
		frm[value_field.name] = value_field
		
		return frm
	
	def update_storable(self, req, frm, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		form_name = '%s-form' % storable.get_table()
		if(form_name in req.data):
			form_data = req.data[form_name]
			if not(form_data.get(self.name, {}).get('%s-autocomplete' % self.name, form.nil()).value):
				setattr(storable, self.get_column_name(), None)
			elif(self.name in form_data and self.name in form_data[self.name]):
				setattr(storable, self.get_column_name(), form_data[self.name][self.name].value)
		return True


class ForeignMultipleSelectField(define.definition):
	"""
	Allow management of an n2m relationship with a foreign table.
	"""
	implements(IDatatype)
	
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		mlabel = self.get('flabel', '')
		if(mlabel.find('.') == -1):
			mlabel = 'm.%s' % mlabel
		mlabel = self.get('flabel_sql', mlabel)
		
		where = self.get('fwhere', '')
		
		if(callable(where)):
			where = where(storable)
		if(isinstance(where, dict)):
			where = sql.build_where(where)
		
		ntom_query = """SELECT m.%s AS value, %s AS label, IF(n2m.%s, 1, 0) AS selected
						FROM %s m
						LEFT JOIN %s n2m ON m.%s = n2m.%s AND n2m.%s = %%s
						%s
						ORDER BY label""" % (self['fvalue'], q(mlabel), self['ntof_f_id'],
										  q(self['ftable']),
										  q(self['ntof']), self.get('fvalue', 'id'),
										  self['ntof_f_id'], self['ntof_n_id'],
										  where)
		
		store = storable.get_store()
		results = store.pool.runQuery(ntom_query, storable.get_id())

		if(style == 'listing' or self.get('read_only', False)):
			label_value = ', '.join([item['label'] for item in results if item['selected']])
			return form.FormNode(self.name)(type='label', value=label_value)
		
		values = [item['value'] for item in results if item['selected']]
		options = OrderedDict([(item['value'], item['label']) for item in results])
		
		frm = form.FormNode(self.name)
		frm(type='select', multiple=True, value=values, options=options)
		return frm
	
	def update_storable(self, req, form, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		form_data = req.data[form.name]
		store = storable.get_store()
		item_id = storable.get_id()
		
		delete_query = sql.build_delete(self['ntof'], {self['ntof_n_id']:item_id})
		store.pool.runOperation(delete_query)
		
		if(self.name in form_data):
			values = form_data[self.name].value
			if not(isinstance(values, list)):
				values = [values]
			data = [{self['ntof_n_id']:item_id, self['ntof_f_id']:val} for val in values]
			insert_query = sql.build_insert(self['ntof'], data)
			store.pool.runOperation(insert_query)
		elif(self.get('required', False)):
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
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		return True

class ForeignMultipleAutocompleteField(ForeignMultipleSelectField):
	"""
	Allow management of an n2m relationship with a foreign table by using an autocomplete field.
	"""
	def get_element(self, req, style, storable):
		"""
		@see: L{modu.editable.define.definition.get_element()}
		"""
		mlabel = self.get('flabel', '')
		if(mlabel.find('.') == -1):
			mlabel = 'm.%s' % mlabel
		mlabel = self.get('flabel_sql', mlabel)
		
		where = self.get('fwhere', '')
		
		if(callable(where)):
			where = where(storable)
		elif(isinstance(where, dict)):
			where = sql.build_where(where)
		
		limit = 'LIMIT %d' % self.get('limit_choices', 20)
		
		ntom_query = """SELECT m.%s AS value, %s AS label
						FROM %s m
						INNER JOIN %s n2m ON m.%s = n2m.%s AND n2m.%s = %%s
						%s
						ORDER BY label
						%s""" % (self['fvalue'], q(mlabel),
								q(self['ftable']),
								q(self['ntof']), self.get('fvalue', 'id'),
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
		ac_url = req.get_path(req.prepath, 'autocomplete', storable.get_table(), self.name) + '?time=' + str(time.time())
		
		hidden_options = ''
		for value in options:
			hidden_options += tags.input(type='hidden', name='%s[%s]' % (form_name, self.name), value=value)
		
		select_frm = form.FormNode('%s-select-view' % self.name)
		select_frm(type='select', options=options, size=self.get('size', 5),
					multiple=None, suffix=hidden_options + '<br/>', attributes={'id':select_id})
		
		prefs = 'autoFill:1, selectFirst:1, matchSubset:0, selectOnly:1, extraParams:{t:%d}, minChars:%d' % (int(time.time()), self.get('min_chars', 3))
		ac_js = '$("#%s").autocomplete("%s", {onItemSelect:add_foreign_item("%s", "%s"), %s});' % (ac_id, ac_url, form_name, self.name, prefs)
		ac_controls = tags.script(type='text/javascript')[ac_js]
		
		ac_field = form.FormNode('%s-autocomplete' % self.name)
		ac_field(type='textfield', weight=10, attributes={'id':ac_id}, suffix=ac_controls)
		
		req.content.report('header', tags.style(type="text/css")[
			"""@import '%s';""" % req.get_path('/assets/jquery/jquery.autocomplete.css')])
		
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/jquery/jquery-1.2.1.js"))[''])
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/jquery/jquery.autocomplete.js"))[''])
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path("/assets/editable-autocomplete.js"))[''])
		
		frm = form.FormNode('%s-ac-fieldset' % self.name)(type='fieldset', style='brief')
		frm[select_frm.name] = select_frm
		frm[ac_field.name] = ac_field
		
		return frm
