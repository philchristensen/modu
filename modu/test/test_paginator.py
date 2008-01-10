# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import time, sys, copy

from modu.util import test
from modu import persist
from modu.persist import storable, adbapi, page

from twisted.trial import unittest

"""
CREATE DATABASE modu;
GRANT ALL ON modu.* TO modu@localhost IDENTIFIED BY 'modu';
"""

class PaginatorTestCase(unittest.TestCase):
	def setUp(self):
		self.store = persist.Store.get_store()
		if not(self.store):
			pool = adbapi.connect('MySQLdb://modu:modu@localhost/modu')
			self.store = persist.Store(pool)
			#self.store.debug_file = sys.stderr
		
		for sql in test.TEST_TABLES.split(";"):
			if(sql.strip()):
				self.store.pool.runOperation(sql)
		
		self.store.ensure_factory('page', force=True)
		
		for i in range(105):
			s = storable.Storable('page')
			s.code = 'url-code-%d' % self.store.fetch_id(s)
			s.content = 'The quick brown fox jumps over the lazy dog.'
			s.title = 'Old School'
			self.store.save(s)
		
	def tearDown(self):
		pass
	
	def test_total_records(self):
		count_result = self.store.pool.runQuery('SELECT COUNT(*) AS total_items FROM page')
		self.failUnlessEqual(count_result[0]['total_items'], 105, "Found too many sample records: %d" % count_result[0]['total_items'])
	
	def test_paginate_calc(self):
		p = page.Paginator()
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(p.total_results, 105, "Paginator has incorrect total results: %d" % p.total_results)
		self.failUnlessEqual(p.start_range, 1, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 10, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 10, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator()
		p.page = 2
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(p.total_results, 105, "Paginator has incorrect total results: %d" % p.total_results)
		self.failUnlessEqual(p.start_range, 11, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 20, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 10, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator()
		p.per_page = 25
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(p.total_results, 105, "Paginator has incorrect total results: %d" % p.total_results)
		self.failUnlessEqual(p.start_range, 1, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 25, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 25, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator()
		p.page = 4
		p.per_page = 25
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(p.total_results, 105, "Paginator has incorrect total results: %d" % p.total_results)
		self.failUnlessEqual(p.start_range, 76, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 100, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 25, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator()
		p.page = 5
		p.per_page = 25
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(p.total_results, 105, "Paginator has incorrect total results: %d" % p.total_results)
		self.failUnlessEqual(p.start_range, 101, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 105, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 5, "Paginator returned wrong number of results: %d" % len(pages))
	
	def test_paginate_nocalc(self):
		p = page.Paginator(False)
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(str(p.total_results), '10+', "Paginator has incorrect total results: %s" % p.total_results)
		self.failUnlessEqual(p.start_range, 1, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 10, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 10, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator(False)
		p.page = 2
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(str(p.total_results), '20+', "Paginator has incorrect total results: %s" % p.total_results)
		self.failUnlessEqual(p.start_range, 11, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 20, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 10, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator(False)
		p.per_page = 25
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(str(p.total_results), '25+', "Paginator has incorrect total results: %s" % p.total_results)
		self.failUnlessEqual(p.start_range, 1, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 25, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 25, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator(False)
		p.page = 4
		p.per_page = 25
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(str(p.total_results), '100+', "Paginator has incorrect total results: %s" % p.total_results)
		self.failUnlessEqual(p.start_range, 76, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 100, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 25, "Paginator returned wrong number of results: %d" % len(pages))
		
		p = page.Paginator(False)
		p.page = 5
		p.per_page = 25
		pages = p.get_results(self.store, 'page', {})
		
		self.failUnlessEqual(p.total_results, 105, "Paginator has incorrect total results: %s" % p.total_results)
		self.failUnlessEqual(p.start_range, 101, "Paginator has incorrect start range: %d" % p.start_range)
		self.failUnlessEqual(p.end_range, 105, "Paginator has incorrect end range: %d" % p.end_range)
		self.failUnlessEqual(len(pages), 5, "Paginator returned wrong number of results: %d" % len(pages))

