# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.util import tags

class Theme(object):
	def form(self, form):
		content = ''
		for child in form:
			content += self.form_element(form[child], form)
			content += "\n"
		
		attribs = form.attrib('attributes', {})
		attribs['name'] = form.name
		attribs['enctype'] = form.attrib('enctype', 'application/x-www-form-urlencoded')
		return tags.form(**attribs)["\n" + content]
	
	def form_element(self, element, form):
		attribs = element.attrib('attributes', {})
		attribs['name'] = '%s[%s]' % (form.name, element.name)
		
		output = ''
		if(element.type == 'textfield'):
			attribs['size'] = element.attrib('size', 30)
			attribs['type'] = 'text'
			output = tags.input(**attribs)
		elif(element.type == 'textarea'):
			attribs['cols'] = element.attrib('cols', 40)
			attribs['rows'] = element.attrib('rows', 5)
			output = tags.textarea(**attribs)['']
		else:
			raise ValueError("Unknown form element type '%s'" % element.type)
		
		return tags.div(class_='form-item')[tags.label()[element.desc] + output]
