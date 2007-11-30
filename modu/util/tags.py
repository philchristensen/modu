# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from htmlentitydefs import name2codepoint, codepoint2name
import re

entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")

def decode_htmlentities(string):
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

def encode_htmlentities(string):
	if not(isinstance(string, basestring)):
		return string
	result = ''
	for c in string:
		cp = ord(c)
		if(cp in codepoint2name):
			result += '&%s;' % codepoint2name[cp]
		else:
			result += c
	return result

def quote(string):
	if not(isinstance(string, basestring)):
		return string
	return string.replace('"', '&quot;')

class Tag(object):
	def __init__(self, tag):
		self.tag = tag
		self.attributes = {}
		self.children = []
	
	def __getitem__(self, children):
		if not(isinstance(children, (list, tuple))):
			children = [children]
		self.children.extend(children)
		return self
	
	def __call__(self, *args, **kwargs):
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
		output = '<' + self.tag
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
				output += str(child)
			if not(self.attributes.get('_no_close', False)):
				output += '</%s>' % self.tag
		else:
			if(self.attributes.get('_no_close', False)):
				output += '>'
			else:
				output += ' />'
		
		return output
	
	def __add__(self, other):
		return str(self) + str(other)
	
	def __radd__(self, other):
		return str(other) + str(self)
	
	def __eq__(self, other):
		return str(self) == str(other)


class _tag(str):
	"""_tag is a string subclass. Instances of _tag, which are constructed
	with a string, will construct Tag instances in response to __call__
	and __getitem__, delegating responsibility to the tag.
	"""
	def __call__(self, **kw):
		return Tag(self)(**kw)
	
	def __getitem__(self, children):
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

