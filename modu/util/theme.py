# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import copy

from modu.util import tags, OrderedDict

class Theme(object):
	def __init__(self, req):
		self.req = req
	
	
	def form(self, form):
		content = ''
		for child in form:
			content += self.form_element(form.name, form[child])
			content += "\n"
		
		attribs = form.attr('attributes', {})
		attribs['name'] = form.name.replace('-', '_')
		attribs['id'] = form.name
		attribs['enctype'] = form.attr('enctype', 'application/x-www-form-urlencoded')
		attribs['method'] = form.attr('method', 'post')
		attribs['action'] = form.attr('action', '')
		
		action = form.attr('action', None)
		if(action):
			attribs['action'] = action
		return tags.form(**attribs)["\n" + content]
	
	
	def form_element(self, form_id, element):
		content = ''
		
		if(hasattr(element, 'label')):
			content += tags.label(_class="field-label")[element.label]
		
		content += self.basic_form_element(form_id, element)
		
		if(hasattr(element, 'help')):
			content += tags.div(_class='form-help')[element.help]
		
		if(element.get_errors()):
			element_class = 'form-item form-error'
		else:
			element_class = 'form-item'
		
		return tags.div(_class=element_class, _id='form-item-%s' % element.name)[content]
	
	
	def basic_form_element(self, form_id, element):
		content = ''
		prefix = element.attr('prefix', False)
		if(callable(prefix)):
			content += prefix(element)
		elif(prefix):
			content += str(prefix)
		
		if(element.attr('type', False)):
			theme_func = getattr(self, 'form_' + element.type)
		else:
			theme_func = self.form_markup
		
		content += theme_func(form_id, element)
		
		suffix = element.attr('suffix', False)
		if(callable(suffix)):
			content += suffix(element)
		elif(suffix):
			content += str(suffix)
		
		return content
	
	
	def form_markup(self, form_id, element):
		return element.attr('value', '')
	
	
	def form_fieldset(self, form_id, element):
		element_style = element.attr('style', 'brief')
		if(element_style == 'full'):
			return ''.join([str(self.form_element(form_id, element[child])) for child in element])
		else:
			content = ''
			for child_name in element:
				content += self.basic_form_element(form_id, element[child_name])
			return content
	
	
	def form_label(self, form_id, element):
		attribs = element.attr('attributes', {})
		value = element.attr('value', element.attr('default_value', ''))
		return tags.label(**attribs)[value]
	
	
	def form_hidden(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = element.attr('value', element.attr('default_value', ''))
		return tags.input(type='hidden', **attribs)
	
	
	def form_textfield(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['size'] = element.attr('size', 30)
		attribs['value'] = element.attr('value', element.attr('default_value', ''))
		return tags.input(type='text', **attribs)
	
	
	def form_password(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['size'] = element.attr('size', 30)
		attribs['value'] = element.attr('value', element.attr('default_value', ''))
		return tags.input(type='password', **attribs)
	
	
	def form_textarea(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['cols'] = element.attr('cols', 40)
		attribs['rows'] = element.attr('rows', 5)
		return tags.textarea(**attribs)[element.attr('value', element.attr('default_value', ''))]
	
	
	def form_submit(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = element.attr('value', 'Submit')
		return tags.input(type='submit', **attribs)
	
	
	def form_checkbox(self, form_id, element):
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
	
	
	def form_radio(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		attribs['value'] = element.attr('value', 1)
		if(element.attr('selected', False)):
			attribs['checked'] = None
		return tags.input(type='radio', **attribs)
	
	
	def form_select(self, form_id, element):
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
			option_data[''] = 'Select...'
		
		def _create_option(k):
			tag = tags.option(value=k)[option_data[k]]
			if(str(k) in value):
				tag(selected=None)
			return tag
		
		options = map(_create_option, option_keys)
		
		if not(options):
			options = ' '
		
		return tags.select(**attribs)[options]
	
	
	def form_radiogroup(self, form_id, element):
		attribs = element.attr('attributes', {})
		attribs['name'] = element.get_element_name()
		
		comparator = element.attr('sort', cmp)
		
		options_clone = copy.copy(element.attr('options', []))
		option_keys, option_data = self._mangle_option_data(options_clone, comparator)
		
		element = [str(tags.label()[[
			tags.input(type='radio', value=key),
			option_data[key]
		]]) for key in option_keys]
		
		return ''.join(element)
	
	
	def _mangle_option_data(self, option_data, comparator):
		if(isinstance(option_data, dict)):
			option_keys = option_data.keys()
		else:
			option_keys = [i for i in range(len(option_data))]
			option_data = dict(zip(option_keys, option_data))
		
		if not(isinstance(option_data, OrderedDict)):
			option_keys.sort(comparator)
		
		return (option_keys, option_data)
	
	
	def form_timestamp(self, form_id, element):
		style = element.attr('style', 'date')
		if(style == 'date' or style == 'datetime'):
			pass
		if(style == 'datetime' or style == 'time'):
			pass
		
	
	def form_date(self, form_id, element):
		pass
	
	
	def form_file(self, form_id, element):
		pass
	
	
	def form_image(self, form_id, element):
		pass
	
	
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
