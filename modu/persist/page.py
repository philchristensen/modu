# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Utilities to paginate result sets.
"""

import copy

from modu.persist import Store

class Paginator(object):
	"""
	This class provides a wrapper around store.load
	to allow paginating Storable results.
	"""
	
	def __init__(self, calc_found=True):
		"""
		Create a Paginator object. If calc_found is True (the default),
		this will calculate the true number of results, at the cost of
		a most expensive DB query.
		"""
		self.calc_found = calc_found
		
		self.page = 1
		self.per_page = 10
		self.total_results = 0
		self.start_range = 0
		self.end_range = 0
	
	def get_results(self, store, *args, **kwargs):
		"""
		Load objects from the given store. This method will
		return a maximum of self.per_page results, while
		setting up all the other variables of the instance.
		"""
		args = copy.deepcopy(args)
		kwargs = copy.deepcopy(kwargs)
		
		# FIXME: Make sure this works reasonably with both
		# attribute dictionaries and direct queries
		if(self.calc_found):
			kwargs['__select_keyword'] = 'SQL_CALC_FOUND_ROWS'
		
		kwargs['__limit'] = self.get_limit()
		
		results = store.load(*args, **kwargs)
		self.start_range = ((self.page - 1) * self.per_page) + 1
		
		if(self.calc_found):
			found_result = store.pool.runQuery("SELECT FOUND_ROWS() AS found_rows")
			self.total_results = found_result[0]['found_rows']
			self.end_range = self.start_range + len(results) - 1
		else:
			self.total_results = self.start_range
			self.end_range = self.start_range + len(results) - 2
			if(len(results) <= self.per_page):
				self.end_range += 1
				self.total_results += len(results) - 1
			else:
				results.pop()
				self.total_results = str(self.end_range) + '+'
		
		if not(len(results)):
			self.start_range = 0
			self.end_range = 0
		
		return results
	
	def get_limit(self):
		"""
		Return the LIMIT clause this class will generate for the
		next query, so developers can easily write their own
		complex queries.
		"""
		start = ((self.page - 1) * self.per_page)
		if(self.calc_found):
			return '%d,%d' % (start, self.per_page)
		else:
			# request one extra so we know there's more
			return '%d,%d' % (start, self.per_page + 1)
	
	def has_next(self):
		"""
		Return true if this Paginator thinks there are
		more results.
		"""
		if(self.calc_found):
			return self.end_range < self.total_results
		else:
			return str(self.total_results).endswith('+')
	
	def has_previous(self):
		"""
		Return true if this Paginator thinks we are on
		a greater page than 1.
		"""
		return self.start_range > 1
