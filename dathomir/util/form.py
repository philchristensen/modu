# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import re, cgi, rfc822, time

try:
	import cStringIO as StringIO
except:
	import StringIO

NESTED_NAME = re.compile(r'([^\[]+)(\[([^\]]+)\])*')
KEYED_FRAGMENT = re.compile(r'\[([^\]]+)\]*')

class FormNode(object):
	"""
	In an attempt to mimic the Drupal form-building process in a slightly more
	Pythonic way, this class allows you to populate a Form object using
	dictionary-like syntax.
	
	Note that this will simply create a form definition. Separate classes/modules
	will need to be used to render the form.
	"""
	
	def __init__(self, name):
		self.name = name
		self.parent = None
		self.children = {}
		self.attributes = {}
		
		self.submit = None
		self.theme = None
		self.validate = None
	
	def __call__(self, *args, **kwargs):
		if('clobber' in kwargs and kwargs['clobber']):
			del kwargs['clobber']
			self.attributes = kwargs
			return
		
		for key, value in kwargs.iteritems():
			if(key in ('theme', 'validate', 'submit')):
				if not(callable(value)):
					raise TypeError("'%s' must be a callable object" % key)
				setattr(self, key, value)
			else:
				self.attributes[key] = value
	
	def __getitem__(self, key):
		if(key not in self.children):
			if(self.parent is not None and self.attributes['type'] != 'fieldset'):
				raise TypeError('Only forms and fieldsets can have child fields.')
			self.children[key] = FormNode(key)
			self.children[key].parent = self
		return self.children[key]

class NestedFieldStorage(cgi.FieldStorage):
	"""
	NestedFieldStorage allows you to use a dict-like syntax for
	naming your form elements. This allows related values to be
	grouped together, and retrieved as a single dict.

	(who'd'a thunk it, stealing from PHP...)
	"""
	def __init__(self, req, parent=None, fp=None, headers=None, outerboundary="",
					environ=None, keep_blank_values=True, strict_parsing=False):
		self.__nested_table_cache = {}
		self.req = req
		self.parent = parent
		if(fp is None):
			fp = req['wsgi.input']
		if(environ is None):
			environ = req
		cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
									environ, keep_blank_values, strict_parsing)
	
	def __getattr__(self, name):
		if name != 'value':
			raise AttributeError, name
		if self.file:
			self.file.seek(0)
			value = self.file.read()
			self.file.seek(0)
		elif self.list is not None:
			value = self.list
		else:
			value = None
		return value

	def parse_field(self, key, value):
		original_key = key
		tree = []
		
		match = NESTED_NAME.match(key)
		if(match is not None):
			tree.append(match.group(1))
			matches = KEYED_FRAGMENT.findall(key)
			tree.extend(matches)
		
		new = False
		if(len(tree) > 1):
			key = tree[0]
			node = self.__nested_table_cache
			# iterate through the key list
			try:
				while(tree):
					fragment = tree.pop(0)
					if(fragment in node):
						if(tree):
							if(isinstance(node[fragment], dict)):
								node = node[fragment]
							else:
								raise ValueError('bad naming scheme')
						else:
							raise ValueError('bad naming scheme')
					else:
						if(node == self.__nested_table_cache):
							new = True
						if(tree):
							node[fragment] = {}
							node = node[fragment]
						else:
							node[fragment] = value
			except ValueError:
				# Some kind of collision, just keep the
				# original key
				# item = util.StringField(value)
				# item.name = original_key
				# self.list.append(item)
				return (original_key, value, True)
			else:
				if(new):
					# item = DictField(self.__nested_table_cache[key])
					# item.name = key
					# self.list.append(item)
					return (key, self.__nested_table_cache[key], True)
				else:
					return (key, self.__nested_table_cache[key], False)
		else:
			# item = util.StringField(value)
			# item.name = key
			# self.list.append(item)
			return (key, value, True)
	
	
	def read_urlencoded(self):
		"""Internal: read data in query string format."""
		self.req.log_error('read_urlencoded()')
		qs = self.fp.read(self.length)
		self.list = list = []
		for key, value in cgi.parse_qsl(qs, self.keep_blank_values,
									self.strict_parsing):
			key, value, new = self.parse_field(key, value)
			
			part = cgi.MiniFieldStorage(key, value)
			name, value, new = self.parse_field(part.name, part)
			if(new):
				if(isinstance(value, dict)):
					item = DictField(value)
				else:
					item = value
				item.name = name
				self.list.append(item)
		
		self.skip_lines()
	
	
	def read_multi(self, environ, keep_blank_values, strict_parsing):
		"""Internal: read a part that is itself multipart."""
		self.req.log_error('read_multi()')
		ib = self.innerboundary
		if not cgi.valid_boundary(ib):
			raise ValueError, 'Invalid boundary in multipart form: %r' % (ib,)
		self.list = []
		part = NestedFieldStorage(self.req, self, self.fp, {}, ib,
					 environ, keep_blank_values, strict_parsing)
		# Throw first part away
		while not part.done:
			headers = rfc822.Message(self.fp)
			part = NestedFieldStorage(self.req, self, self.fp, headers, ib,
						 environ, keep_blank_values, strict_parsing)
			
			name, value, new = self.parse_field(part.name, part)
			if(new):
				if(isinstance(value, dict)):
					item = DictField(value)
				else:
					item = value
				item.name = name
				self.list.append(item)
		
		self.skip_lines()
	
	
	def make_file(self, binary=None):
		self.req.log_error('make_file()')
		if(self.filename):
			return MagicFile(self.req, self.filename, 'w+b')
		else:
			import tempfile
			return tempfile.TemporaryFile("w+b")
	

class MagicFile(file):
	def __init__(self, req, filename, mode='r', bufsize=-1):
		import tempfile, md5, os.path
		hashed_filename = os.path.join(tempfile.gettempdir(), md5.new(filename + time.ctime()).hexdigest())
		file.__init__(self, hashed_filename, mode, bufsize)
		
		self.req = req
		self.req.log_error('saving to ' + hashed_filename)
		self.client_filename = filename
		session = self.req['dathomir.session']
		if('dathomir.file' not in session):
			session['dathomir.file'] = {}
		
		session['dathomir.file'][self.client_filename] = {'bytes_written':0, 'total_bytes':self.req['CONTENT_LENGTH']}
		session.save()
	
	def write(self, data):
		session = self.req['dathomir.session']
		file_state = session['dathomir.file'][self.client_filename]
		
		file_state['bytes_written'] += len(data)
		session.save()
		
		super(MagicFile, self).write(data)
	
	def seek(self, offset, whence=0):
		self.req.log_error('file was sought')
		session = self.req['dathomir.session']
		session['dathomir.file'][self.client_filename]['complete'] = 1
		super(MagicFile, self).seek(offset, whence)

class DictField(dict):
	def __init__(self, value):
		dict.__init__(self)
		self.update(value)
