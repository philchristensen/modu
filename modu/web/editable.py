# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id: twist.py 414 2007-08-09 19:52:15Z phil $
#
# See LICENSE for details

from zope.interface import implements, Interface, Attribute

from modu.util import form
from modu.persist import storable

class IEditable(storable.IStorable):
	def get_itemdef(self):
		"""
		Return an object/datastructure representing the
		fields and behaviors for this object's editable
		forms.
		"""

class itemdef(dict):
	def __init__(self, **kwargs):
		for k, v in kwargs.iteritems():
			if not(isinstance(v, definition)):
				raise ValueError("'%s' is not a valid definition." % k)
			
		self.update(kwargs)

class definition(dict):
	def __init__(self, **kwargs):
		self.update(kwargs)

sample_itemdef = itemdef(
	__special		= definition(
						postwrite_callback			= 'user_postwrite',
						prewrite_callback			= 'user_prewrite'
					),
	
	id				= definition(
						postwrite_callback			= 'user_postwrite',
						prewrite_callback			= 'user_prewrite'
					)
)