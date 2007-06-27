# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.web.modpython import handler
from dathomir.web import app, resource
from dathomir.util import form, theme

import os, time

def sample_form(req):
	frm = form.FormNode(req, 'node-form')
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

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		frm = sample_form(req)
		frm.submit = self.submit_form
		self.set_slot('form', frm.render())
		self.set_slot('result_data', '(none)')
		if(req.has_form_data()):
			frm.execute()
	
	def submit_form(self, req, frm):
		data = form.NestedFieldStorage(req)
		self.set_slot('result_data', str(data['node-form']))
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl'

app.base_url = '/dathomir/examples/form'
app.activate(RootResource())
