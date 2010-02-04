# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

from htmlentitydefs import name2codepoint, codepoint2name
import re

entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")
reserved2name = {
	ord('"')  : 'quot',
	ord(u'"') : 'quot',
	ord('>')  : 'gt',
	ord(u'>') : 'gt',
	ord('<')  : 'lt',
	ord(u'<') : 'lt'
}

def filter_entities(item):
	"""
	Recurse through a standard data structure and replace all
	ampersands and double-quotes HTML entities.
	"""
	if(isinstance(item, basestring)):
		return item.replace('&', '&amp;').replace('"', "&quot;")
	elif(isinstance(item, (list, tuple))):
		if(isinstance(item, tuple)):
			item = list(item)
		for index in range(len(item)):
			item[index] = filter_entities(item[index])
		return item
	elif(isinstance(item, dict)):
		for key, value in item.items():
			item[key] = filter_entities(item[key])
		return item
	else:
		print item.get_data()
		raise ValueError("Unsupported item type: %r" % item)

def decode_htmlentities(string):
	"""
	Decode HTML entities into their Unicode equivalent.
	"""
	def __entity(match):
		ent = match.group(2)
		if match.group(1) == "#":
			return unichr(int(ent))
		else:
			cp = name2codepoint.get(ent)
		
			if cp:
				return unichr(cp)
			else:
				return match.group()
	
	return entity_re.subn(__entity, string)[0]

def encode_htmlentities(string, strict=False):
	"""
	Encode special characters in `string` into HTML entities.
	
	If strict is True, encode **all** possible entities.
	"""
	if(isinstance(string, str)):
		result = ''
	elif(isinstance(string, unicode)):
		result = u''
	else:
		return string
	
	for c in string:
		cp = ord(c)
		if(strict and cp in codepoint2name):
			result += '&%s;' % codepoint2name[cp]
		elif(cp in reserved2name):
			result += '&%s;' % reserved2name[cp]
		else:
			result += c
	return result

def quote(string):
	"""
	Replace double-quotes in `string` with '&quot;'
	"""
	if not(isinstance(string, basestring)):
		return string
	return string.replace('"', '&quot;')

class Tag(object):
	"""
	An X/HTML tag.
	"""
	def __init__(self, tag):
		"""
		Create a new tag with the given name.
		"""
		self.tag = tag
		self.attributes = {}
		self.children = []
	
	def __getitem__(self, children):
		"""
		Item access indicates containment.
		"""
		if not(isinstance(children, (list, tuple))):
			children = [children]
		self.children.extend(children)
		return self
	
	def __call__(self, *args, **kwargs):
		"""
		Call syntax indicates attributes.
		"""
		if not(kwargs):
			return self
		
		for key, value in kwargs.iteritems():
			if key[-1] == '_':
				key = key[:-1]
			elif key[0] == '_':
				key = key[1:]
			self.attributes[key] = value
		
		return self
	
	def __str__(self):
		return self.stringify(str)
	
	def __unicode__(self):
		return self.stringify(unicode)
	
	def stringify(self, stringtype):
		"""
		Render as ASCII.
		"""
		output = stringtype()
		output += '<' + self.tag
		fragments = ''
		keys = self.attributes.keys()
		keys.sort()
		for key in keys:
			if not(key.startswith('_')):
				value = self.attributes[key]
				if(value is None):
					fragments += ' %s' % key
				else:
					output += ' %s="%s"' % (key, quote(value))
		output += fragments
		if(self.children):
			output += '>'
			for child in self.children:
				output += stringtype(child)
			if not(self.attributes.get('_no_close', False)):
				output += '</%s>' % self.tag
		else:
			if(self.attributes.get('_no_close', False)):
				output += '>'
			else:
				output += ' />'
		
		return output
	
	def __add__(self, other):
		"""
		Concatenation support.
		"""
		return str(self) + str(other)
	
	def __radd__(self, other):
		"""
		Concatenation support.
		"""
		return str(other) + str(self)
	
	def __eq__(self, other):
		"""
		Equality support.
		"""
		return str(self) == str(other)


class _tag(str):
	"""_tag is a string subclass. Instances of _tag, which are constructed
	with a string, will construct Tag instances in response to __call__
	and __getitem__, delegating responsibility to the tag.
	"""
	def __call__(self, **kw):
		"""
		Convienience syntax.
		"""
		return Tag(self)(**kw)
	
	def __getitem__(self, children):
		"""
		Convienience syntax.
		"""
		return Tag(self)[children]


_tags = [
'a','abbr','acronym','address','applet','area','b','base','basefont','bdo','big','blockquote',
'body','br','button','caption','center','cite','code','col','colgroup','dd','dfn','div',
'dl','dt','em','fieldset','font','form','frame','frameset','h1','h2','h3','h4','h5','h6','head',
'hr','html','i','iframe','img','input','ins','isindex','kbd','label','legend','li','link','menu',
'meta','noframes','noscript','ol','optgroup','option','p','param','pre','q','s','samp',
'script','select','small','span','strike','strong','style','sub','sup','table','tbody','td','textarea',
'tfoot','th','thead','title','tr','tt','u','ul','var'
]

_globs = globals()
for t in _tags:
	_globs[t] = _tag(t)

