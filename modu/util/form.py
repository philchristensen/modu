# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import re, cgi, rfc822, time, copy

try:
	import cStringIO as StringIO
except:
	import StringIO

from modu.util import theme

NESTED_NAME = re.compile(r'([^\[]+)(\[([^\]]+)\])*')
KEYED_FRAGMENT = re.compile(r'\[([^\]]+)\]*')

def nil():
	"""
	A convenience method for testing values in a NestedFieldStorage object.
	
	This allows a developer to use C{nfs['my-form'].get('title', form.nil()).value is None}
	"""
	return cgi.MiniFieldStorage('nil-field', None)


class FormNode(object):
	"""
	In an attempt to mimic the Drupal form-building process in a slightly more
	Pythonic way, this class allows you to populate a Form object using
	dictionary- and call-like syntax.
	
	Note that this will simply create a form definition. Separate classes/modules
	will need to be used to render the form.
	"""
	
	def __init__(self, name):
		self.name = name
		self.parent = None
		self.children = {}
		self.attributes = {}
		
		self.errors = {}
		
		self.submit = self._submit
		self.validate = self._validate
		self.theme = theme.Theme
		self.data = {}
		
		self.submit_button = None
	
	def __getattr__(self, name):
		"""
		A convenience method for accessing form attributes.
		"""
		if(name in self.attributes):
			return self.attributes[name]
		raise AttributeError(name)
	
	def __call__(self, *args, **kwargs):
		"""
		This call method allows the syntax (attr=value, attr2=value2, etc...).
		If the boolean 'clobber' is True, the provided attribs replace any
		currently set in the form node.
		"""
		if('clobber' in kwargs and kwargs['clobber']):
			del kwargs['clobber']
			self.attributes = kwargs
			return self
		
		for key, value in kwargs.iteritems():
			if(key in ('theme', 'validate', 'submit')):
				if not(callable(value)):
					raise TypeError("'%s' must be a callable object" % key)
				setattr(self, key, value)
			else:
				self.attributes[key] = value
		return self
	
	def __getitem__(self, key):
		"""
		Allows child selection via hash syntax.
		"""
		if(key not in self.children):
			if('type' in self.attributes):
				if(self.parent is not None and self.attributes['type'] != 'fieldset'):
					raise TypeError('Only forms and fieldsets can have child fields.')
			else:
				self.attributes['type'] = 'fieldset'
			self[key] = FormNode(key)(weight=len(self.children))
		return self.children[key]
	
	def __nonzero__(self):
		"""
		All forms are nonzero.
		"""
		return True
	
	def __setitem__(self, key, child):
		"""
		Allows insertion of child forms.
		"""
		self.children[key] = child
		child.name = key
		child.parent = self
	
	def __delitem__(self, key):
		"""
		Child form deletion.
		"""
		del self.children[key]
	
	def __len__(self):
		"""
		Return number of child form elements.
		"""
		return len(self.children)
	
	def __iter__(self):
		"""
		Iterate through child form names.
		"""
		return self.iterkeys()
	
	def __contains__(self, key):
		"""
		Implement containment for child names.
		"""
		return key in self.children
	
	def iterkeys(self):
		"""
		Order key results by weight.
		"""
		def __weighted_cmp(a, b):
			a = self.children[a]
			b = self.children[b]
			return cmp(a.attr('weight', 0), b.attr('weight', 0))
		
		keys = self.children.keys()
		keys.sort(__weighted_cmp)
		return iter(keys)
	
	def attr(self, name, default=None):
		"""
		Similar to dict.get(), for form attributes.
		"""
		if(name in self.attributes):
			return self.attributes[name]
		if(name == 'name'):
			return self.name
		return default
	
	def get_element_path(self):
		"""
		Return list of names from parent to this item.
		"""
		path = []
		node = self
		while(node is not None):
			path.append(str(node.name))
			node = node.parent
		path.reverse()
		return path
	
	def get_element_name(self):
		"""
		Get this element's HTML form name.
		"""
		path = self.get_element_path()
		return '%s[%s]' % (path[0], ']['.join(path[1:]))
	
	def has_submit_buttons(self):
		"""
		See if a submit button has been defined in this form.
		"""
		for name in self.children:
			element = self.children[name]
			if(element.type == 'submit'):
				return True
			elif(element.children):
				if(element.has_submit_buttons()):
					return True
		return False
	
	def find_submit_buttons(self):
		"""
		Return any submit buttons in this form.
		
		This method descends down the form tree looking for
		form elements of the type 'submit', and returns an
		array of results.
		"""
		submits = []
		for name in self.children:
			element = self.children[name]
			if(element.type == 'submit'):
				submits.append(element)
			elif(element.children):
				submits.extend(element.find_submit_buttons())
		return submits
	
	def execute(self, req, force=False):
		"""
		Process this form.
		
		This function first identifies 	whether or not a submit button
		was pressed. If so, it begins the validation process, then, if
		successful, initiates the submission process.
		"""
		self.data = NestedFieldStorage(req)
		
		for submit in self.find_submit_buttons():
			# NOTE: This assumes the browser sends the submit button's name
			# in the submit POST data. This may not always work.
			if(self.name in self.data and submit.name in self.data[self.name]):
				self.submit_button = submit
				break
		
		if(self.submit_button or force):
			self.load_data(req, self.data)
			result = self.validate(req, self)
			if(result):
				return self.submit(req, self)
		
		return False
	
	def set_error(self, name, error):
		"""
		Note an error with this form's child.
		
		This function may only be called on top-level forms.
		"""
		if(self.parent):
			raise RuntimeError('Errors cannot be set directly on child form elements.')
		self.errors.setdefault(name, []).append(error)
	
	def has_errors(self):
		"""
		Return true if this form or any of its children have errors.
		"""
		return bool(len(self.get_errors()))
	
	def get_errors(self):
		"""
		Return errors on this element.
		
		If this is a top-level form, return all errors. Otherwise, only
		return errors from this form.
		"""
		item = self
		errors = {}
		while(True):
			if(item.parent):
				item = item.parent
			else:
				break
		
		if(item == self):
			return item.errors
		else:
			return item.errors.get(self.name)
	
	def render(self, req):
		"""
		This method calls the appropriate theme functions against
		this form and request, and returns HTML for display.
		"""
		thm = self.theme(req)
		return thm.form(self)
	
	def load_data(self, req, data):
		"""
		This function takes a FieldStorage object (more often
		NestedFieldStorage) and populates this form.
		
		This is invoked automatically by C{execute()}. Keep in mind that
		this means that if a post value *looks* like it belongs to a form
		(i.e., it is nested under the form's name), that form element will
		have its 'value' attribute set to the post value.
		"""
		if(self.name in data):
			form_data = data[self.name]
			if(isinstance(form_data, dict)):
				if(self.children):
					for name, child in self.children.items():
						child.load_data(req, form_data)
				else:
					# this would happen if a theme function
					# generated nested form data for a single
					# form object
					loader = self.attr('loader', None)
					loader_func = 'form_%s_loader' % self.attr('type', 'markup')
					if(not loader and hasattr(self.theme, loader_func)):
						loader = getattr(self.theme(req), loader_func, None)
					if(callable(loader)):
						loader(self, form_data)
			else:
				if(hasattr(form_data, 'value')):
					self.attributes['value'] = form_data.value
				else:
					self.attributes['value'] = form_data
	
	def _validate(self, req, form):
		"""
		This is the default validation function. If not overriden
		by setting the validate attribute, this will call validate()
		on all children. If any return false, validation fails for
		this form.
		
		Note that in this case `self` and `form` refer to the same
		object. This is so that when a custom validation function is
		supplied, it still gets a reference to the form instance
		it was called for.
		"""
		result = True
		
		for child in self.children:
			child = self.children[child]
			result = result and child.validate(req, form)
		
		return result
	
	def _submit(self, req, form):
		"""
		Forms have no default bahavior for submission, so if no
		submit attribute has been set on this form, an error is raised.
		"""
		raise NotImplementedError("FormNode('%s')::submit" % self.name)


class FieldStorageDict(dict):
	"""
	Sometimes it's convenient to deal with field storage as if
	it were a real dict.
	"""
	
	def __init__(self, field_storage):
		self.field_storage = field_storage
	
	def __getitem__(self, key):
		if(key in self.field_storage):
			return self.field_storage[key].value
		return dict.__getitem__(self, key)
	
	def __contains__(self, key):
		if(key in self.field_storage):
			return True
		return dict.__contains__(self, key)
	
	def __len__(self):
		return len(self.field_storage) + dict.__len__(self)
	
	def keys(self):
		return self.field_storage.keys() + dict.keys(self)


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
			if(hasattr(fp, 'seek')):
				fp.seek(0)
		if(environ is None):
			environ = req
		cgi.FieldStorage.__init__(self, fp, headers, outerboundary,
									environ, keep_blank_values, strict_parsing)
	
	def __nonzero__(self):
		"""
		Fixes a bug in cgi.py
		"""
		if(self.list):
			return True
		elif(self.value):
			return True
		else:
			return False
	
	def get(self, key, default=None):
		"""
		Implements dict-style .get() function.
		"""
		if(key in self):
			return self[key]
		return cgi.MiniFieldStorage(key, default)
	
	def parse_field(self, key, value):
		"""
		This method manages the storage of nested data.
		"""
		#print 'parse field got %s: %s' % (key, value)
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
					#print 'key is %s, fragment is %s, value is %s, tree is %s' % (key, fragment, value, tree)
					if(fragment in node):
						if(tree):
							if(isinstance(node[fragment], dict)):
								node = node[fragment]
							else:
								raise ValueError('bad naming scheme')
						else:
							if(isinstance(node[fragment], dict)):
								raise ValueError('bad naming scheme')
							elif(isinstance(node[fragment].value, list)):
								node[fragment].value.append(value.value)
							else:
								node[fragment].value = [node[fragment].value, value.value]
					else:
						if(node == self.__nested_table_cache):
							#print 'found a new entry'
							new = True
						if(tree):
							#print 'found a new namespace'
							node[fragment] = DictField()
							node = node[fragment]
						else:
							#print 'adding %s to namespace %s as %s' % (value, node, fragment)
							node[fragment] = value
							#self.req.log_error('node is now: ' + str(node))
			except ValueError:
				# Some kind of collision, just keep the original key
				return (original_key, value, True)
			else:
				if(new):
					# No existing top-level form name
					return (key, self.__nested_table_cache[key], True)
				else:
					# The top-level name has been added, and we've already
					# manipulated its child hash references
					return (key, self.__nested_table_cache[key], False)
		else:
			# No nested field names found, use the normal behavior
			return (key, value, True)
	
	
	def read_urlencoded(self):
		"""Internal: read data in query string format."""
		#print ('read_urlencoded()',)
		qs = self.fp.read(self.length)
		self.list = list = []
		for key, value in cgi.parse_qsl(qs, self.keep_blank_values,
									self.strict_parsing):
			part = cgi.MiniFieldStorage(key, value)
			name, value, new = self.parse_field(part.name, part)
			if(new):
				value.name = name
				self.list.append(value)
		
		self.skip_lines()
	
	
	def read_multi(self, environ, keep_blank_values, strict_parsing):
		"""Internal: read a part that is itself multipart."""
		#print ('read_multi()',)
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
				value.name = name
				self.list.append(value)
		
		self.skip_lines()
	
	
	def make_file(self, binary=None):
		"""
		Enables use of MagicFile for progressive file transfers.
		"""
		if(self.filename):
			return MagicFile(self.req, self.filename, 'w+b')
		else:
			import tempfile
			return tempfile.TemporaryFile("w+b")
	

class DictField(dict):
	"""
	Used to provided nested POST data in C{NestedFieldStorage}.
	"""
	def __init__(self, value=None):
		dict.__init__(self)
		if(value):
			self.update(value)


class MagicFile(file):
	"""
	This wrapper class will log all the bytes written to it into the user's
	session object. This allows for progressive upload information to be
	polled for by the client.
	"""
	def __init__(self, req, filename, mode='r', bufsize=-1):
		"""
		Create a new MagicFile.
		"""
		import tempfile, md5, os.path
		hashed_filename = os.path.join(tempfile.gettempdir(), md5.new(filename + time.ctime()).hexdigest())
		file.__init__(self, hashed_filename, mode, bufsize)
		
		self.req = req
		self.client_filename = filename
		session = self.req.session
		if('modu.file' not in session):
			session['modu.file'] = {}
		
		session['modu.file'][self.client_filename] = {'bytes_written':0, 'total_bytes':self.req['CONTENT_LENGTH']}
		session.touch()
		session.save()
	
	def write(self, data):
		"""
		Write to the file and update the session bytecount.
		"""
		# So, we automatically save the session every time a page is
		# loaded, since we need to update the access time. So writing
		# the pickled data repeatedly (as we update the bytes written)
		# is really only a bad thing because of the pickling overhead.
		session = self.req.session
		file_state = session['modu.file'][self.client_filename]
		#print "writing: %d bytes" % len(data)
		file_state['bytes_written'] += len(data)
		session.touch()
		session.save()
		
		super(MagicFile, self).write(data)
	
	def seek(self, offset, whence=0):
		"""
		When seek goes to 0, we must be done loading the file.
		"""
		#self.req.log_error('file was sought')
		session = self.req.session
		session['modu.file'][self.client_filename]['complete'] = 1
		super(MagicFile, self).seek(offset, whence)
