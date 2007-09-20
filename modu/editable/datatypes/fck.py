# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Contains the FCK Editor support for modu.editable.
"""

import os, os.path, time, stat, shutil, StringIO

from zope.interface import implements

from modu import editable, persist
from modu.editable import define
from modu.util import form, tags
from modu.web import resource, app

SUCCESS 			= 0
CUSTOM_ERROR		= 1

UL_RENAME			= 201
UL_INVALID_TYPE		= 202
UL_ACCESS_DENIED	= 203

FLD_EXISTS			= 101
FLD_INVALID_NAME	= 102
FLD_ACCESS_DENIED	= 103
FLD_UNKNOWN_ERROR	= 110

class FCKEditorField(define.definition):
	implements(editable.IDatatype)
	
	def get_element(self, req, style, storable):
		frm = form.FormNode(self.name)
		if(style == 'listing'):
			frm(type='label', value='(html content)')
			return frm
		if(self.get('read_only', False)):
			frm(type='label', value=getattr(storable, self.name, ''))
			return frm
		
		fck_base_path = req.get_path('assets', 'fckeditor')
		req.content.report('header', tags.script(type="text/javascript",
			src=req.get_path('assets', 'fckeditor', 'fckeditor.js'))[''])
		
		fck_custom_config = req.get_path(self.get('fck_root', '/fck'), 'fckconfig-custom.js')
		fck_element_name = '%s-form[%s]' % (storable.get_table(), self.name)
		
		# //$value = str_replace("'", '&apos;', $value);
		fck_value = getattr(storable, self.name, '')
		fck_value = fck_value.replace("\r\n", r'\r\n')
		fck_value = fck_value.replace("\n", r'\n')
		fck_value = fck_value.replace("\r", r'\r')
		fck_value = fck_value.replace('"', r'\"')
		
		
		fck_var = 'fck_%s' % self.name
		output = tags.script(type="text/javascript")[[
				"var %s = new FCKeditor('%s');\n" % (fck_var, fck_element_name),
				"%s.Config['CustomConfigurationsPath'] = \"%s\";\n" % (fck_var, fck_custom_config),
				"%s.BasePath = \"%s/\";\n" % (fck_var, fck_base_path),
				"%s.Value = \"%s\";\n" % (fck_var, fck_value),
				"%s.Width = \"%s\";\n" % (fck_var, self.get('width', 600)),
				"%s.Height = \"%s\";\n" % (fck_var, self.get('height', 400)),
				"%s.ToolbarSet = \"%s\";\n" % (fck_var, self.get('toolbar_set', 'Standard')),
				"%s.Create();\n" % fck_var
			]]
		
		frm(type="markup", value=output)
		return frm
	
	
	def get_search_value(self, value):
		if(self.get('fulltext_search')):
			return persist.RAW(persist.interp("MATCH(%%s) AGAINST (%s)", [value]))
		else:
			return persist.RAW(persist.interp("INSTR(%%s, %s)", [value]))


class FCKEditorResource(resource.CheetahTemplateResource):
	def __init__(self, **options):
		self.upload_dir = options.get('upload_dir', '/Users/phil/Workspace/dram2/webroot')
		self.upload_url = options.get('upload_url', '/')
	
	
	def get_paths(self):
		return ['/fck']
	
	
	def prepare_content(self, req):
		self.content_type = 'text/html'
		self.content = None
		self.template = None
		try:
			if(req.postpath):
				if(req.postpath[0] == 'fckconfig-custom.js'):
					self.prepare_config_request(req)
				elif(req.postpath[0] == 'upload'):
					self.prepare_quick_upload(req)
				else:
					self.prepare_browser(req)
			else:
				self.prepare_browser(req)
		except:
			import traceback
			traceback.print_exc()
	
	
	def get_content_type(self, req):
		return '%s; charset=UTF-8' % self.content_type
	
	
	def get_content(self, req):
		if(self.content):
			return self.content
		return super(FCKEditorResource, self).get_content(req)
	
	
	def get_template(self, req):
		return self.template
	
	
	def get_template_root(self, req):
		import modu
		template = self.get_template(req)
		
		template_root = os.path.join(req.approot, 'template')
		if(os.access(os.path.join(template_root, template), os.F_OK)):
			return template_root
		
		return os.path.join(os.path.dirname(modu.__file__), 'assets', 'default-template')
	
	
	def prepare_quick_upload(self, req):
		result, filename = self.handle_upload(req, self.upload_dir)
		file_url = os.path.join(self.upload_url, filename)
		
		self.content = [str(tags.script(type="text/javascript")[
						"window.parent.OnUploadCompleted(%s, '%s', '%s', '');\n" % (result, file_url, filename)
						])]
	
	
	def prepare_browser(self, req):
		data = form.NestedFieldStorage(req)
		
		if(req['REQUEST_METHOD'] == 'POST'):
			get_data = form.NestedFieldStorage({'QUERY_STRING':req['QUERY_STRING'],
												'wsgi.input':req['wsgi.input']})
		else:
			get_data = data
		
		command_name = get_data.get('Command').value
		resource_type = get_data.get('Type').value
		new_folder_name = get_data.get('NewFolderName').value
		folder_path = get_data.get('CurrentFolder').value
		if(folder_path is None):
			folder_path = ''
		elif(folder_path.startswith('/')):
			folder_path = folder_path[1:]
		
		folder_url = os.path.join(self.upload_url, folder_path)
		
		content = tags.Tag('CurrentFolder')(path=folder_path, url=folder_url)
		
		if(command_name == 'GetFolders'):
			content += self.get_directory_items(folder_path, True)
		elif(command_name == 'GetFoldersAndFiles'):
			content += self.get_directory_items(folder_path, False)
		elif(command_name == 'CreateFolder'):
			content += self.create_folder(folder_path, new_folder_name)
		elif(command_name == 'FileUpload'):
			self.file_upload(req, folder_path)
			return
		else:
			return
		
		output = '<?xml version="1.0" encoding="utf-8" ?>'
		output += tags.Tag('Connector')(command=command_name, resourceType=resource_type)[str(content)]
		
		self.content_type = 'text/xml'
		self.content = [output]
	
	
	def prepare_config_request(self, req):
		self.content_type = 'text/javascript'
		self.template = 'fckconfig-custom.js.tmpl'
	
	
	def get_directory_items(self, folder_path, folders_only):
		folder_content = ''
		file_content = ''
		
		directory_path = os.path.join(self.upload_dir, folder_path)
		for item in os.listdir(directory_path):
			full_path = os.path.join(directory_path, item)
			finfo = os.stat(full_path)
			if(stat.S_ISREG(finfo.st_mode)):
				file_content += tags.Tag('File')(name=item, size=(finfo.st_size // 1024))
			else:
				folder_content += tags.Tag('Folder')(name=item)
		
		content = tags.Tag('Folders')[folder_content]
		if(not folders_only and file_content):
			content += tags.Tag('Files')[file_content]
		
		return content
	
	
	def create_folder(self, folder_path, new_folder_name):
		directory_path = os.path.join(self.upload_dir, folder_path)
		
		#prevent shenanigans
		new_folder_name = new_folder_name.split('/').pop()
		
		new_path = os.path.join(directory_path, new_folder_name)
		if(os.access(new_path, os.F_OK)):
			content = tags.Tag('Error')(number=FLD_EXISTS)
		else:
			try:
				os.mkdir(new_path)
				content = tags.Tag('Error')(number=SUCCESS)
			except:
				content = tags.Tag('Error')(number=FLD_UNKNOWN_ERROR)
		
		return content
	
	
	def file_upload(self, req, folder_path):
		result, filename = self.handle_upload(req, folder_path)
		file_url = os.path.join(self.upload_url, folder_path, filename)
		
		self.content_type = 'text/html'
		self.content = [str(tags.script(type="text/javascript")[
						"window.parent.frames['frmUpload'].OnUploadCompleted(%s, '%s');\n" % (result, filename)
						])]
	
	def handle_upload(self, req, folder_path):
		result = UL_ACCESS_DENIED
		
		data = form.NestedFieldStorage(req)
		fileitem = data['NewFile']
		
		filename = fileitem.filename
		destination_path = os.path.join(self.upload_dir, folder_path, filename)
		if(os.access(destination_path, os.F_OK)):
			parts = filename.split('.')
			if(len(parts) > 1):
				parts[len(parts) - 2] += '-%d' % int(time.time())
				filename = '.'.join(parts)
				result = UL_RENAME
			else:
				result = UL_INVALID_TYPE
		if(result != UL_INVALID_TYPE):
			try:
				uploaded_file = open(destination_path, 'w')
				bytes = fileitem.file.read(65536)
				while(bytes):
					uploaded_file.write(bytes)
					bytes = fileitem.file.read(65536)
				uploaded_file.close()
				result = SUCCESS
			except:
				import traceback
				print traceback.print_exc()
				result = UL_ACCESS_DENIED
		
		return result, filename

