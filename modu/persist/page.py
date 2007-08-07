# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.persist import Store

class Paginator(object):
	def __init__(self, calc_found=True):
		self.calc_found = calc_found
		
		self.page = 1
		self.per_page = 10
		self.total_results = 0
		self.start_range = 0
		self.end_range = 0
	
	def get_results(self, store, *args, **kwargs):
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
		
		return results
	
	def get_limit(self):
		start = ((self.page - 1) * self.per_page)
		if(self.calc_found):
			return '%d,%d' % (start, self.per_page)
		else:
			# request one extra so we know there's more
			return '%d,%d' % (start, self.per_page + 1)
	
	def has_next(self):
		if(self.calc_found):
			return self.end_range < self.total_results
		else:
			return str(self.total_results).endswith('+')
	
	def has_previous(self):
		return self.start_range > 1
