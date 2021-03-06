# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

from twisted.trial import unittest

from modu.util import url

class URLNodeTestCase(unittest.TestCase):
	def setUp(self):
		self.tree = url.URLNode('ROOT')
		self.tree.register('/', 'SLASH')
		self.tree.register('/one', 'ONE')
		self.tree.register('/one/two', 'TWO')
		self.tree.register('/three', 'THREE')
		self.tree.register('/this/is/a/long/url', 'LONG')
		self.tree.register('/test/another/one', 'test1')
		self.tree.register('/test', 'test2')
	
	def tearDown(self):
		pass
	
	def test_root(self):
		result, prepath, postpath = self.tree.parse('/')
		self.failUnlessEqual(result, 'SLASH', "Didn't find 'SLASH' where I expected")
	
	def test_one(self):
		result, prepath, postpath = self.tree.parse('/one/and/some/extra/crud')
		self.failUnlessEqual(result, 'ONE', "Didn't find 'ONE' where I expected")
		
	def test_two(self):
		result, prepath, postpath = self.tree.parse('/one/two/some/extra/crud')
		self.failUnlessEqual(result, 'TWO', "Didn't find 'TWO' where I expected")
		
	def test_three(self):
		result, prepath, postpath = self.tree.parse('/three')
		self.failUnlessEqual(result, 'THREE', "Didn't find 'THREE' where I expected")
		
	def test_slash(self):
		result, prepath, postpath = self.tree.parse('/something/else')
		self.failUnlessEqual(result, 'SLASH', "Didn't find 'SLASH' where I expected")
		
	def test_long(self):
		result, prepath, postpath = self.tree.parse('/this/is/a/long/url')
		self.failUnlessEqual(result, 'LONG', "Didn't find 'LONG' where I expected")
	
	def test_collision(self):
		tree = url.URLNode()
		tree.register('/one', 'ONE')
		self.failUnlessRaises(ValueError, tree.register, '/one', 'TWO')
	
	def test_bug1(self):
		tree = url.URLNode()
		tree.register('/', 'SLASH')
		result, prepath, postpath = tree.parse('/status')
		self.failUnlessEqual(result, 'SLASH', "Root resource was not returned properly")
	
	def test_bug2(self):
		tree = url.URLNode()
		self.failIf(tree.has_path('/modu/examples/multisite/cheetah'), 'tree.has_path() is broken')
		tree.register('/modu/examples/multisite/cheetah', 'MSCHEETAH')
		self.failUnless(tree.has_path('/modu/examples/multisite/cheetah'), 'tree.has_path() is broken')
		
		self.failIf(tree.has_path('/modu/examples/multisite/basic'), 'tree.has_path() is broken')
		tree.register('/modu/examples/multisite/basic', 'MSBASIC')
		self.failUnless(tree.has_path('/modu/examples/multisite/basic'), 'tree.has_path() is broken')

		self.failIf(tree.has_path('/modu/examples/cheetah'), 'tree.has_path() is broken')
		tree.register('/modu/examples/cheetah', 'CHEETAH')
		self.failUnless(tree.has_path('/modu/examples/cheetah'), 'tree.has_path() is broken')
		
		self.failIf(tree.has_path('/modu/examples/basic'), 'tree.has_path() is broken')
		tree.register('/modu/examples/basic', 'BASIC')
		self.failUnless(tree.has_path('/modu/examples/basic'), 'tree.has_path() is broken')
	
