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
			content += self.form_element(form[child], form)
			content += "\n"
		
		attribs = form.attrib('attributes', {})
		attribs['name'] = form.name
		attribs['enctype'] = form.attrib('enctype', 'application/x-www-form-urlencoded')
		attribs['method'] = form.attrib('method', 'post')
		return tags.form(**attribs)["\n" + content]
	
	def form_element(self, form_id, element):
		content = ''
		if(hasattr(element, 'label')):
			content += tags.label()[element.label]
		
		if(element.attrib('type', False)):
			theme_func = getattr(self, 'form_' + element.type)
		else:
			theme_func = self.form_markup
		
		content += theme_func(form_id, element)
		
		if(hasattr(element, 'help')):
			content += tags.div(_class='form-help')[element.help]
		
		return tags.div(_class='form-item')[content]
	
	def form_markup(self, form_id, element):
		return element.attrib('value', '')
	
	def form_text(self, form_id, element):
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
		return tags.input(type='text', **attribs)
	
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
		attribs['value'] = element.attrib('value', 1)
		
		option_data = element.attrib('options', [])
		if(isinstance(option_data, dict)):
			option_data = option_data.items()
		else:
			option_data = [(i,option_data[i]) for i in range(len(option_data))]
		options = map(lambda(i): tags.option(value=i[0])[i[1]], option_data)
		return tags.select(type='radio', **attribs)["\n".join(options)]
	
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
