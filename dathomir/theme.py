# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.util import tags

class Theme(object):
	def render(self, type, *args, **kwargs):
		"""
		Should we be using a top-level theme function?
		"""
		pass
	
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
	
	def form_element(self, element, form):
		content = ''
		if(hasattr(element, 'label')):
			content += tags.label()[element.label]
		
		theme_func = getattr(self, 'form_' + element.type, self.form_markup)
		content += theme_func(element, form)
		
		if(hasattr(element, 'help')):
			content += tags.div(class_='form-help')[element.help]
		
		return tags.div(class_='form-item')[content]
	
	def form_markup(self, element, form):
		return element.attrib('value', '')
	
	def form_textfield(self, element, form):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form.name, element.name)
		attribs['size'] = element.attrib('size', 30)
		attribs['type'] = 'text'
		return tags.input(**attribs)
	
	def form_textarea(self, element, form):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form.name, element.name)
		attribs['cols'] = element.attrib('cols', 40)
		attribs['rows'] = element.attrib('rows', 5)
		return tags.textarea(**attribs)['']
	
	def form_submit(self, element, form):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form.name, element.name)
		attribs['value'] = element.attrib('value', 'Submit')
		return tags.input(type='submit', **attribs)
