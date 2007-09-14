# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Various utilities useful in building modu applications.
"""

from twisted.python import util

class OrderedDict(util.OrderedDict):
	def __init__(self, dict=None, *args, **kwargs):
		self._order = []
		self.data = {}
		if dict is not None:
			if hasattr(dict,'keys'):
				self.update(dict)
			else:
				for k,v in dict: # sequence
					self[k] = v
		if len(args):
			for a in args:
				self[a[0]] = a[1]
		if len(kwargs):
			self.update(kwargs)
