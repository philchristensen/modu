# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from dathomir.app import handler
from dathomir import app, resource, theme
from dathomir.util import form

import os, time

def node_form():
	frm = form.FormNode('node-form')
	frm['title'](desc='Title',
				 type='textfield',
				 weight=-20;
				 size=30,
				 help='Enter the title of this entry here.'
				)
	frm['body'](desc='Body',
				type='textarea',
				weight=0,
				cols=30,
				rows=10,
				help='Enter the body text as HTML.'
				)
	frm.submit = node_submit
	frm.theme = theme.Theme()
	return frm

def node_submit(req, form):
	pass

class RootResource(resource.CheetahTemplateResource):
	def get_paths(self):
		return ['/']
	
	def prepare_content(self, req):
		frm = node_form()
		self.add_slot('form', frm.theme.form(frm))
		if(req.is_post()):
			if(frm.validate(req, frm)):
				frm.submit(req, frm)
	
	def get_content_type(self, req):
		return 'text/html'
	
	def get_template(self, req):
		return 'page.html.tmpl'

app.base_url = '/dathomir/examples/form'
app.activate(RootResource())
