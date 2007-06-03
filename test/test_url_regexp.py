#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest

from dathomir.util import url

class URLRegExpTestCase(unittest.TestCase):
	def test_full(self):
		result = url.urlparse('http://user:password@example.com:1234/a/long/path;params?one=1&two=2#ch01');
		self.failUnlessEqual(result['scheme'], 'http', "Didn't find 'scheme' where I expected")
		self.failUnlessEqual(result['user'], 'user', "Didn't find 'user' where I expected")
		self.failUnlessEqual(result['password'], 'password', "Didn't find 'password' where I expected")
		self.failUnlessEqual(result['host'], 'example.com', "Didn't find 'host' where I expected")
		self.failUnlessEqual(result['port'], '1234', "Didn't find 'port' where I expected")
		self.failUnlessEqual(result['path'], '/a/long/path', "Didn't find 'path' where I expected")
		self.failUnlessEqual(result['params'], 'params', "Didn't find 'params' where I expected")
		self.failUnlessEqual(result['query'], 'one=1&two=2', "Didn't find 'query' where I expected")
		self.failUnlessEqual(result['fragment'], 'ch01', "Didn't find 'fragment' where I expected")
	
	def test_dsn(self):
		result = url.urlparse('mysql://user:password@localhost/database');
		self.failUnlessEqual(result['scheme'], 'mysql', "Didn't find 'scheme' where I expected")
		self.failUnlessEqual(result['user'], 'user', "Didn't find 'user' where I expected")
		self.failUnlessEqual(result['password'], 'password', "Didn't find 'password' where I expected")
		self.failUnlessEqual(result['host'], 'localhost', "Didn't find 'host' where I expected")
		self.failUnlessEqual(result['path'], '/database', "Didn't find 'path' where I expected")
	
	def test_svn_ssh(self):
		result = url.urlparse('svn+ssh://svn.dathomir.org/svnroot/dathomir/trunk');
		self.failUnlessEqual(result['scheme'], 'svn+ssh', "Didn't find 'scheme' where I expected")
		self.failUnlessEqual(result['host'], 'svn.dathomir.org', "Didn't find 'host' where I expected")
		self.failUnlessEqual(result['path'], '/svnroot/dathomir/trunk', "Didn't find 'path' where I expected")
	
if __name__ == "__main__":
	unittest.main()
