# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import copy, datetime

from modu.util import tags, OrderedDict, date
from modu import assets

def formelement(func):
	def _form_render(self, form_id, form):
		return self.theme_element(form_id, form, func(self, form_id, form))
	return _form_render

class Theme(object):
	def __init__(self, req):
		self.req = req
	
	def theme_form(self, form_id, element):
		content = ''
		for child_id in element:
			child = element[child_id]
			theme = child.get_theme(self.req, current=self)
			theme_func = getattr(theme, 'theme_' + child.attr('type', 'fieldset'))
			content += theme_func(element.name, child)
			content += "\n"
		
		attribs = element.attr('attributes', {})
		attribs['name'] = element.name.replace('-', '_')
		attribs['id'] = element.name
		attribs['enctype'] = element.attr('enctype', 'application/x-www-form-urlencoded')
		attribs['method'] = element.attr('method', 'post')
		attribs['action'] = element.attr('action', '')
		
		action = element.attr('action', None)
		if(action):
			attribs['action'] = action
		
		result = element.attr('prefix', '')
		result += tags.form(**attribs)["\n" + content]
		result += element.attr('suffix', '')
		
		return result
	
	def theme_element(self, form_id, element, rendered_element):
		content = ''
		
		if not(element.attr('basic_element', False)):
			if(element.attr('required', False)):
				asterisk = tags.span(_class="required")['*']
			else:
				asterisk = ''
			
			if(hasattr(element, 'label')):
				content += tags.label(_class="field-label")[[element.label, asterisk]]
			
		prefix = element.attr('prefix', False)
		if(callable(prefix)):
			content += prefix(element)
		elif(prefix):
			content += str(prefix)
		
		content += rendered_element
			
		suffix = element.attr('suffix', False)
		if(callable(suffix)):
			content += suffix(element)
		elif(suffix):
			content += str(suffix)
		
		if not(element.attr('basic_element', False)):
			if(hasattr(element, 'help')):
				content += tags.div(_class='form-help')[element.help]
			
			displays_errors = False
			if(element.attr('type', 'fieldset') != 'fieldset' or element.attr('style', 'brief') == 'brief'):
				displays_errors = True
			
			if(displays_errors and element.has_errors()):
				element_class = 'form-item form-error'
			else:
				element_class = 'form-item'
			
			item_id = 'form-item-%s' % element.name
			if(element.attr('deep_form_ids', False, recurse=True)):
				item_id = 'form-item-%s' % '-'.join(element.get_element_path())
			content = tags.div(_class=element_class, _id=item_id)[content]
		
		return content
	
	@formelement
	def theme_markup(self, form_id, element):
		return element.attr('value', '') or ''
	
	@formelement
	def theme_fieldset(self, form_id, element):
		element_style = element.attr('style', 'brief')
		content = ''
		for child_id in element:
			child = element[child_id]
			theme = child.get_theme(self.req, current=self)
		
			theme_func = getattr(theme, 'theme_' + child.attr('type', 'fieldset'))
			
			if(element_style != 'full'):
				child(basic_element=True)
			
			content += theme_func(element.name, child)
		
		return content
	
	@formelement
	def theme_label(self, form_id, element):
		attribs = element.attr('attributes', {'class':'label'})
		value = element.attr('value', element.attr('default_value', ''))
		if(value is None):
			value = ''
		return tags.span(**attribs)[value]
	
	@formelement
	def theme_hidden(self, form_id, element):
		# note that we still use formelement, even though it seems
		# unintuitive. this allows us to make label-esque fields
		# with a hidden form element
		value = element.attr('value', element.attr('default_value', ''))
		if(value is None):
			value = ''
		
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = value
		return tags.input(type='hidden', **attribs)
	
	def theme_value(self, form_id, element):
		# a 'value' form type is used to store server-side content
		return ''
	
	@formelement
	def theme_textfield(self, form_id, element):
		value = element.attr('value', element.attr('default_value', ''))
		if(value is None):
			value = ''
		
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['size'] = element.attr('size', 30)
		attribs['value'] = value
		return tags.input(type='text', **attribs)
	
	@formelement
	def theme_file(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		return tags.input(type='file', **attribs)
	
	@formelement
	def theme_password(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['size'] = element.attr('size', 30)
		attribs['value'] = element.attr('value', element.attr('default_value', ''))
		return tags.input(type='password', **attribs)
	
	@formelement
	def theme_textarea(self, form_id, element):
		value = element.attr('value', element.attr('default_value', ''))
		if(value is None):
			value = ''
		
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['cols'] = element.attr('cols', 40)
		attribs['rows'] = element.attr('rows', 5)
		return tags.textarea(**attribs)[value]
	
	@formelement
	def theme_submit(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = element.attr('value', 'Submit')
		return tags.input(type='submit', **attribs)
	
	@formelement
	def theme_checkbox(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = element.attr('value', 1)
		if(element.attr('checked', False)):
			attribs['checked'] = None
		if(element.attr('disabled', False)):
			attribs['disabled'] = None
		return tags.label()[[
			tags.input(type='checkbox', **attribs),
			element.attr('text', '')
		]]
	
	@formelement
	def theme_radio(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = element.attr('value', 1)
		if(element.attr('selected', False)):
			attribs['checked'] = None
		return tags.input(type='radio', **attribs)
	
	@formelement
	def theme_select(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		if(element.attr('multiple', False)):
			attribs['size'] = element.attr('size', 5)
			attribs['multiple'] = None
		else:
			attribs['size'] = element.attr('size', 1)
		
		value = element.attr('value', 1)
		if not(isinstance(value, (list, tuple))):
			value = [value]
		value = map(str, value)
		
		comparator = element.attr('sort', cmp)
		
		options_clone = copy.copy(element.attr('options', []))
		option_keys, option_data = self._mangle_option_data(options_clone, comparator)
		
		if(attribs['size'] == 1):
			option_keys.insert(0, '')
			option_data[''] = element.attr('null_text', 'Select...')
			del attribs['size']
		
		def _create_option(k):
			tag = tags.option(value=k)[option_data[k]]
			if(str(k) in value):
				tag(selected=None)
			return tag
		
		options = map(_create_option, option_keys)
		
		if not(options):
			options = ' '
		
		return tags.select(**attribs)[options]
	
	@formelement
	def theme_select_autocomplete(self, form_id, element):
		self.req.content.report('header', tags.script(type="text/javascript",
			src=assets.get_jquery_path(self.req))[''])
		self.req.content.report('header', tags.script(type="text/javascript",
			src=self.req.get_path("/assets/jquery/jquery.autocomplete.js"))[''])
		self.req.content.report('header', tags.script(type="text/javascript",
			src=self.req.get_path("/assets/editable-autocomplete.js"))[''])
		
		self.req.content.report('header', tags.style(type="text/css")[
			"""@import '%s';""" % self.req.get_path('/assets/jquery/jquery.autocomplete.css')])
		
		self.req.content.report('header', tags.script(type="text/javascript")[
			"""
			function formatItem(item, index, totalItems){
				return item[0].replace('<', '&lt;').replace('>', '&gt;')
			}
			"""
		])
		ac_id = '%s-%s-autocomplete' % (form_id, element.name)
		ac_cb_id = '%s-%s-ac-callback' % (form_id, element.name)
		
		options = element.attr('options', [])
		optlist = repr([[v, k] for k, v in options.items()])
		
		prefs = dict(
			autoFill	= 1,
			selectFirst	= 1,
			matchSubset	= 0,
			selectOnly	= 1,
			formatItem	= 'formatItem',
		)
		prefs = ','.join(['%s:%s' % (k, v) for k, v in prefs.items()])
		
		ac_javascript = tags.script(type='text/javascript')[
			'$("#%s").autocompleteArray(%s, {onItemSelect:select_item("%s"), %s});' % (ac_id, optlist, ac_cb_id, prefs)
		]
		
		value = element.attr('value')
		if(value):
			label = options.get(value, None)
			if(label is None):
				label = value
			output = tags.input(type="text", name=element.get_element_name() + '[ac]', id=ac_id, value=label)
			output += tags.input(type="hidden", name=element.get_element_name() + '[value]', id=ac_cb_id, value=value)
		else:
			output = tags.input(type="text", name=element.get_element_name() + '[ac]', id=ac_id)
			output += tags.input(type="hidden", name=element.get_element_name() + '[value]', id=ac_cb_id)
		output += ac_javascript
		
		return output
	
	def theme_select_autocomplete_loader(self, form, form_data):
		value = form_data['value'].value
		options = form.attr('options', {})
		ac_label = form_data['ac'].value
		
		if(options.get(value, None) != ac_label):
			value = ac_label
		
		form(value=value)
	
	@formelement
	def theme_radiogroup(self, form_id, element):
		comparator = element.attr('sort', cmp)
		options_clone = copy.copy(element.attr('options', []))
		option_keys, option_data = self._mangle_option_data(options_clone, comparator)
		
		def _create_radio(value, default_value):
			attribs = {}
			if(str(value) == str(default_value)):
				attribs['checked'] = None
			attribs['value'] = value
			attribs['type'] = 'radio'
			attribs['name'] = element.get_element_name()
			return tags.input(**attribs)
		
		element = [str(tags.label()[[
			_create_radio(key, element.attr('value', None)),
			' ', option_data[key]
		]]) for key in option_keys]
		
		return tags.div(_class="radio-group")[''.join(element)]
	
	
	def _mangle_option_data(self, option_data, comparator):
		if(isinstance(option_data, dict)):
			option_keys = option_data.keys()
		else:
			option_keys = [i for i in range(len(option_data))]
			option_data = dict(zip(option_keys, option_data))
		
		if not(isinstance(option_data, OrderedDict)):
			option_keys.sort(comparator)
		
		return (option_keys, option_data)
	
	@formelement
	def theme_timestamp(self, form_id, element):
		style = element.attr('style', 'date')
		if(style == 'date' or style == 'datetime'):
			pass
		if(style == 'datetime' or style == 'time'):
			pass
		
	@formelement
	def theme_datetime(self, form_id, element):
		import time
		attribs = element.attr('attributes', {})
		
		months, days = date.get_date_arrays()
		hours, minutes = date.get_time_arrays()
		
		#value = date.convert_to_timestamp(element.attr('value', None))
		value = element.attr('value', None)
		
		if(value is None):
			year = datetime.datetime.now().year
			month, day, hour, minute = (months[0], 1, '00', '00')
		else:
			month, day, year, hour, minute = date.strftime(value, '%B:%d:%Y:%H:%M').split(':')
		
		arrays = (months, days, hours, minutes)
		values = (month, int(day), hour, minute)
		names = ('month', 'day', 'hour', 'minute')
		
		dateselect = self._generate_datetime_select(element, attribs, arrays[:2], values[:2], names[:2])
		year_attribs = dict(
		 	name = '%s[year]' % element.get_element_name(),
		 	size = 5,
			value = year,
		)
		yearfield = tags.input(type='text', **year_attribs)
		timeselect = self._generate_datetime_select(element, attribs, arrays[2:], values[2:], names[2:])
		
		return ''.join([str(x) for x in (dateselect, yearfield, timeselect)])
	
	def theme_datetime_loader(self, form, form_data):
		import time, datetime
		
		months, days = date.get_date_arrays()
		
		try:
			value = datetime.datetime(int(form_data['year'].value), int(form_data['month'].value) + 1, int(form_data['day'].value) + 1,
										int(form_data['hour'].value), int(form_data['minute'].value))
		except ValueError, e:
			max_day = 30
			if(int(form_data['month'].value) == 2):
				max_day = 28
			value = datetime.datetime(int(form_data['year'].value), int(form_data['month'].value) + 1, max_day,
										int(form_data['hour'].value), int(form_data['minute'].value))
		form(value=value)
	
	@formelement
	def theme_date(self, form_id, element):
		import time
		attribs = element.attr('attributes', {})
		
		months, days = date.get_date_arrays()
		
		value = element.attr('value', None)
		
		if(value is None):
			year = datetime.datetime.now().year
			month, day = (months[0], 1)
		else:
			if(isinstance(value, (int, float))):
				value = datetime.datetime.utcfromtimestamp(value)
			
			month, day, year = date.strftime(value, '%B:%d:%Y').split(':')
		
		arrays = (months, days)
		values = (month, int(day))
		names = ('month', 'day')
		
		monthday = self._generate_datetime_select(element, attribs, arrays, values, names)
		
		yearfield = '%s[year]' % element.get_element_name()
		return str(monthday) + str(tags.input(type='text', size=5, value=year, name=yearfield))
	
	def theme_date_loader(self, form, form_data):
		import time, datetime
		
		months, days = date.get_date_arrays()
		
		try:
			value = datetime.date(int(form_data['year'].value), int(form_data['month'].value) + 1, int(form_data['day'].value) + 1)
		except ValueError:
			max_day = 30
			if(int(form_data['month'].value) == 2):
				max_day = 28
			value = datetime.datetime(int(form_data['year'].value), int(form_data['month'].value) + 1, max_day)
		form(value=value)
	
	@formelement
	def theme_time(self, form_id, element):
		import time
		attribs = element.attr('attributes', {})
		
		hours, minutes = date.get_time_arrays()
		
		value = date.convert_to_timestamp(element.attr('value', None))
		
		if(value is None):
			hour, minute = ('00', '00')
		else:
			hour, minute = time.strftime('%H:%M', time.localtime(value)).split(':')
		
		arrays = (hours, minutes)
		values = (hour, minute)
		names = ('hour', 'minute')
		
		return self._generate_datetime_select(element, attribs, arrays, values, names)
	
	
	def theme_time_loader(self, form, form_data):
		import time, datetime
		
		value = ((int(form_data['hour'].value) * 60) + int(form_data['minute'].value)) * 60
		value += time.timezone
		form(value=value)
	
	
	def _generate_datetime_select(self, element, attribs, arrays, values, names):
		def _create_option(index, v, option_data):
			tag = tags.option(value=index)[option_data[index]]
			if(index == v):
				tag(selected=None)
			return tag
		
		output = ''
		for index in range(len(arrays)):
			selected_item = arrays[index].index(values[index])
			attribs['name'] = '%s[%s]' % (element.get_element_name(), names[index])
			output += tags.select(**attribs)[[
				tags.option(value='')['Select...']
			]+[
				_create_option(i, selected_item, arrays[index]) for i in range(len(arrays[index]))
			]]
		
		return output
	
	
	def page_guide(self, pages, url):
		if(url.find('?') == -1):
			url += '?'
		else:
			from cgi import parse_qs
			from urllib import urlencode
			stub, query = url.split('?')
			query = parse_qs(query)
			if('page' in query):
				del query['page']
			url = '%s?%s&' % (stub, urlencode(query, True))
		
		if(pages.has_previous()):
			prev = tags.span()[tags.a(href="%spage=%d" % (url, pages.page - 1))['&lt;&lt; Previous']]
		else:
			prev = tags.span()['&lt;&lt; Previous']
		
		if(pages.has_next()):
			next = tags.span()[tags.a(href="%spage=%d" % (url, pages.page + 1))['Next &gt;&gt;']]
		else:
			next = tags.span()['Next &gt;&gt;']
		
		return tags.div(_class='page-guide')[[
			tags.div()['Items %d &ndash; %d of %s shown.' %
				(pages.start_range, pages.end_range, pages.total_results)],
			tags.div()[prev, ' | ', next]
		]]
	
