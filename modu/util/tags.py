# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

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
			value = self.attributes[key]
			if(value is None):
				fragments += ' %s' % key
			else:
				output += ' %s="%s"' % (key, value)
		output += fragments
		if(self.children):
			output += '>'
			for child in self.children:
				output += str(child)
			output += '</%s>' % self.tag
		else:
			output += ' />'
		
		return output
	
	def __add__(self, other):
		return str(self) + str(other)
	
	def __radd__(self, other):
		return str(other) + str(self)

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

