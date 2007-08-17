# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.util import tags

class Theme(object):
	def __init__(self, req):
		self.req = req
	
	def form(self, form):
		content = ''
		for child in form:
			content += self.form_element(form.name, form[child])
			content += "\n"
		
		attribs = form.attrib('attributes', {})
		attribs['name'] = form.name.replace('-', '_')
		attribs['id'] = form.name
		attribs['enctype'] = form.attrib('enctype', 'application/x-www-form-urlencoded')
		attribs['method'] = form.attrib('method', 'post')
		
		action = form.attrib('action', None)
		if(action):
			attribs['action'] = action
		return tags.form(**attribs)["\n" + content]
	
	def form_element(self, form_id, element):
		content = ''
		
		if(hasattr(element, 'label')):
			content += tags.label(_class="field-label")[element.label]
		
		content += self._form_element(form_id, element)
		
		if(hasattr(element, 'help')):
			content += tags.div(_class='form-help')[element.help]
		
		return tags.div(_class='form-item', _id='form-item-%s' % element.name)[content]
	
	def _form_element(self, form_id, element):
		content = ''
		prefix = element.attrib('prefix', False)
		if(callable(prefix)):
			content += prefix(element)
		elif(prefix):
			content += str(prefix)
		
		if(element.attrib('type', False)):
			theme_func = getattr(self, 'form_' + element.type)
		else:
			theme_func = self.form_markup
		
		content += theme_func(form_id, element)
		
		suffix = element.attrib('suffix', False)
		if(callable(suffix)):
			content += suffix(element)
		elif(suffix):
			content += str(suffix)
		
		return content
	
	def form_markup(self, form_id, element):
		return element.attrib('value', '')
	
	def form_fieldset(self, form_id, element):
		element_style = element.attrib('style', 'full')
		if(element_style == 'full'):
			return ''.join([str(self.form_element(form_id, element[child])) for child in element])
		else:
			content = ''
			for child_name in element:
				content += self._form_element(form_id, element[child_name])
			return content
	
	def form_label(self, form_id, element):
		attribs = element.attrib('attributes', {})
		value = element.attrib('value', element.attrib('default_value', ''))
		return tags.label(**attribs)[value]
	
	def form_hidden(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['value'] = element.attrib('value', element.attrib('default_value', ''))
		return tags.input(type='hidden', **attribs)
	
	def form_textfield(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['size'] = element.attrib('size', 30)
		attribs['value'] = element.attrib('value', element.attrib('default_value', ''))
		return tags.input(type='text', **attribs)
	
	def form_password(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['size'] = element.attrib('size', 30)
		attribs['value'] = element.attrib('value', element.attrib('default_value', ''))
		return tags.input(type='password', **attribs)
	
	def form_textarea(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['cols'] = element.attrib('cols', 40)
		attribs['rows'] = element.attrib('rows', 5)
		return tags.textarea(**attribs)[element.attrib('value', element.attrib('default_value', ''))]
	
	def form_submit(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['value'] = element.attrib('value', 'Submit')
		return tags.input(type='submit', **attribs)
	
	def form_checkbox(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['value'] = element.attrib('value', 1)
		if(element.attrib('checked', False)):
			attribs['checked'] = None
		return tags.input(type='checkbox', **attribs)
	
	def form_radio(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['value'] = element.attrib('value', 1)
		if(element.attrib('selected', False)):
			attribs['checked'] = None
		return tags.input(type='radio', **attribs)
	
	def form_select(self, form_id, element):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form_id, element.name)
		attribs['size'] = element.attrib('size', 1)
		if('multiple' in element.attributes):
			attribs['multiple'] = element.multiple
		value = element.attrib('value', 1)
		
		option_data = element.attrib('options', [])
		if(isinstance(option_data, dict)):
			option_keys = option_data.keys()
		else:
			option_keys = [i for i in range(len(option_data))]
		
		def _create_option(k):
			tag = tags.option(value=k)[option_data[k]]
			if(k == value):
				tag(selected='selected')
			return tag
		
		option_keys.sort(element.attrib('sort', None))
		options = map(_create_option, option_keys)
		
		if not(options):
			options = ' '
		
		return tags.select(**attribs)[options]
	
	def form_timestamp(self, form_id, element):
		style = element.attrib('style', 'date')
		if(style == 'date' or style == 'datetime'):
			pass
		if(style == 'datetime' or style == 'time'):
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
