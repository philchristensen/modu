# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.web.modpython import handler
from dathomir import app, resource, theme
from dathomir.util import form

import os, time

def sample_form(submit_func):
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
	frm.submit = submit_func
	frm.theme = theme.Theme()
	return frm

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		frm = sample_form(self.submit_form)
		self.set_slot('form', frm.theme.form(frm))
		self.set_slot('result_data', '(none)')
		if(req.has_form_data()):
			frm.execute(req)
	
	def submit_form(self, req, frm):
		data = form.NestedFieldStorage(req)
		self.set_slot('result_data', str(data['node-form']))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl'

app.base_url = '/dathomir/examples/form'
app.activate(RootResource())
