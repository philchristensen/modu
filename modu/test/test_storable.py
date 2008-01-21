# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import time, sys, copy

from modu.util import test
from modu import persist
from modu.persist import storable, adbapi

from twisted.trial import unittest

class StorableTestCase(unittest.TestCase):
	def setUp(self):
		pool = adbapi.connect('MySQLdb://modu:modu@localhost/modu')
		self.store = persist.Store(pool)
		#self.store.debug_file = sys.stderr
		
		for sql in test.TEST_TABLES.split(";"):
			if(sql.strip()):
				self.store.pool.runOperation(sql)
	
	def tearDown(self):
		pass
	
	def test_create(self):
		self.store.ensure_factory('page', force=True)
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		self.failUnless(s.get_id(), 'Storable object has no id after being saved.')
		t = self.store.load_one('page', {'id':s.get_id()});
		
		self.failUnlessEqual(t.get_id(), s.get_id(), 'Column `id` changed in save/load cycle')
		self.failUnlessEqual(t.code, s.code, 'Column `code` changed in save/load cycle')
		self.failUnlessEqual(t.content, s.content, 'Column `content` changed in save/load cycle')
		self.failUnlessEqual(t.title, s.title, 'Column `title` changed in save/load cycle')
	
	def test_destroy(self):
		self.store.ensure_factory('page', force=True)
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		saved_id = s.get_id()
		self.failUnless(saved_id, 'Storable object has no id after being saved.')
		
		self.store.destroy(s)
		t = self.store.load_one('page', {'id':saved_id});
		
		self.failIf(t, 'Storable object was not properly destroyed.')
		self.failIf(s.get_id(), 'Storable object still has an id after being destroyed.')
	
	def test_subclass(self):
		self.store.ensure_factory('page', TestStorable, force=True)
		
		s = TestStorable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		self.failUnless(s.get_id(), 'Storable object has no id after being saved.')
		t = self.store.load_one('page', {'id':s.get_id()});
		
		self.failUnless(isinstance(t, TestStorable), "Loaded object wasn't of the correct type: %r" % t)
		self.failUnlessEqual(t.get_id(), s.get_id(), 'Column `id` changed in save/load cycle')
		self.failUnlessEqual(t.code, s.code, 'Column `code` changed in save/load cycle')
		self.failUnlessEqual(t.content, s.content, 'Column `content` changed in save/load cycle')
		self.failUnlessEqual(t.title, s.title, 'Column `title` changed in save/load cycle')
	
	def test_save_related(self):
		self.store.ensure_factory('page', TestStorable, force=True)
		
		s = TestStorable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		s.populate_related_items(self.store)
		# at this point, the related items are saved,
		# so we can edit them
		self.store.save(s)
		
		for item in s._related:
			item.content = 'updated content'
		
		self.store.save(s)
	
		for item in s._related:
			self.failUnlessEqual(item.content, 'updated content')
	
	def test_destroy_related(self):
		self.store.ensure_factory('page', TestStorable, force=True)
		self.store.ensure_factory('subpage', force=True)
		
		s = TestStorable()
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		s.populate_related_items(self.store)
		# at this point, the related items are saved,
		# so we can DESTROY them! RARRRRGH!!!
		self.store.save(s)
		self.store.destroy(s, True)
	
		orig = self.store.load_one('page', {'code':'url-code'})
		self.failUnless(orig is None, "Found 'url-code' object after destroying it.")
		
		page1 = self.store.load_one('subpage', {'code':'__sample-1__'})
		self.failUnless(page1 is None, "Found '__sample-1__' object after destroying it.")
		
		page2 = self.store.load_one('subpage', {'code':'__sample-2__'})
		self.failUnless(page2 is None, "Found '__sample-2__' object after destroying it.")
		
		page3 = self.store.load_one('subpage', {'code':'__sample-3__'})
		self.failUnless(page3 is None, "Found '__sample-3__' object after destroying it.")
	
	def test_cache(self):
		self.store.ensure_factory('page', force=True, use_cache=True)
		self.failUnless(self.store._factories['page'].use_cache, "Caching wasn't turned on properly")
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.fetch_id(s)
		x = self.store.load_one('page', {'id':s.get_id()});
		self.failIf(x, 'Found unexpected object in DB.')
		
		self.store.save(s)
		
		t = self.store.load_one('page', {'id':s.get_id()});
		self.failUnless(t, 'Cache is saving empty results.')
		
		t.title = 'a whole new title'
		
		u = self.store.load_one('page', {'id':s.get_id()});
		self.failUnlessEqual(u.title, 'a whole new title', "Didn't get cached object when expected (1).")
		
		self.store.pool.runOperation("UPDATE page SET title = 'Old School' WHERE id = %s", [s.get_id()])
		
		v = self.store.load_one('page', {'id':s.get_id()});
		self.failIfEqual(v.title, 'Old School', "Didn't get cached object when expected (2).")
		
	
	def test_nocache(self):
		self.store.ensure_factory('page', force=True)
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		
		t = self.store.load_one('page', {'id':s.get_id()});
		
		t.title = 'a whole new title'
		self.store.save(t)
		
		u = self.store.load_one('page', {'id':s.get_id()});
		self.failUnlessEqual(u.title, t.title, "Got cached object when not expected.")
	
	def test_cached_decorator(self):
		s = TestStorable()
		
		result = s.sample_cached_function()
		self.failUnlessEqual(result, repr(s), "s.sample_cached_function didn't return the cached string")
		self.failUnless(s._sample_calc_ran, "sample_calc hasn't run")
		s._sample_calc_ran = False
		four = s.sample_cached_function()
		
		self.failIf(s._sample_calc_ran, "sample_calc ran again")
		
		t = TestStorable()
		result = t.sample_cached_function()
		self.failUnlessEqual(result, repr(t), "t.sample_cached_function didn't return the cached string")
	
	def _load_by_setup(self):
		self.store.ensure_factory('page', force=True)
		
		s = storable.Storable('page')
		s.code = 'url-code'
		s.content = 'The quick brown fox jumps over the lazy dog.'
		s.title = 'Old School'
		
		self.store.save(s)
		self.failUnless(s.get_id(), 'Storable object has no id after being saved.')
		return s
	
	def test_load_by_storable(self):
		s = self._load_by_setup()
		t1 = self.store.load_one('page', {'id':s.get_id()})
		t2 = self.store.load_one(TrivialTestStorable(), {'id':s.get_id()})
		
		self.failUnlessEqual(t1.__class__, storable.Storable, 'Got back %r when expecting a Storable' % t1.__class__)
		self.failUnlessEqual(t2.__class__, TrivialTestStorable, 'Got back %r when expecting a TrivialTestStorable' % t1.__class__)
	
	def test_load_by_storable_class(self):
		s = self._load_by_setup()
		t1 = self.store.load_one('page', {'id':s.get_id()})
		t2 = self.store.load_one(TrivialTestStorable, {'id':s.get_id()})
		
		self.failUnlessEqual(t1.__class__, storable.Storable, 'Got back %r when expecting a Storable' % t1.__class__)
		self.failUnlessEqual(t2.__class__, TrivialTestStorable, 'Got back %r when expecting a TrivialTestStorable' % t1.__class__)
	
	def test_load_by_factory(self):
		s = self._load_by_setup()
		factory = storable.DefaultFactory('page', model_class=TrivialTestStorable)
		t1 = self.store.load_one('page', {'id':s.get_id()})
		t2 = self.store.load_one(factory, {'id':s.get_id()})
		
		self.failUnlessEqual(t1.__class__, storable.Storable, 'Got back %r when expecting a Storable' % t1.__class__)
		self.failUnlessEqual(t2.__class__, TrivialTestStorable, 'Got back %r when expecting a TrivialTestStorable' % t1.__class__)

class TrivialTestStorable(storable.Storable):
	def __init__(self):
		super(TrivialTestStorable, self).__init__('page')

class TestStorable(storable.Storable):
	def __init__(self):
		super(TestStorable, self).__init__('page')
		self._related = []
		self._sample_calc_ran = False
	
	def populate_related_items(self, store):
		store.ensure_factory('subpage', force=True)
		
		page1 = store.load_one('subpage', {'code':'__sample-1__'})
		if(page1 is None):
			page1 = storable.Storable('subpage')
			page1.code = '__sample-1__'
			page1.content = 'test content'
		
		page2 = store.load_one('subpage', {'code':'__sample-2__'})
		if(page2 is None):
			page2 = storable.Storable('subpage')
			page2.code = '__sample-2__'
			page2.content = 'test content'
		
		page3 = store.load_one('subpage', {'code':'__sample-3__'})
		if(page3 is None):
			page3 = storable.Storable('subpage')
			page3.code = '__sample-3__'
			page3.content = 'test content'
		
		self._related = [page1, page2, page3]
	
	@storable.cachedmethod
	def sample_cached_function(self):
		return self.sample_calc()
	
	def sample_calc(self):
		self._sample_calc_ran = True
		return repr(self)
	
	def sample_function(self):
		return True
	
	def get_related_storables(self):
		return copy.copy(self._related)
		