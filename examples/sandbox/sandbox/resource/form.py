# Modu Sandbox
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

from modu.web import resource
from modu.util import form

def sample_form(req):
	frm = form.FormNode('node-form')
	frm(enctype='multipart/form-data')
	frm['title'](type='textfield',
				 label='Title',
				 weight=-20,
				 size=30,
				 help='Enter the title of this entry here.'
				)
	frm['body'](type='textarea',
				label='Body',
				weight=0,
				cols=30,
				rows=10,
				help='Enter the body text as HTML.'
				)
	frm['submit'](type='submit',
				value='submit',
				weight=100,
				)
	return frm

class Resource(resource.CheetahTemplateResource):
	def prepare_content(self, req):
		frm = sample_form(req)
		frm.submit = self.submit_form
		self.set_slot('result_data', '(none)')
		frm.execute(req)
		self.set_slot('form', frm.render(req))
	
	def submit_form(self, req, frm):
		self.set_slot('result_data', str(frm.data))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'form.html.tmpl'
