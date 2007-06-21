#!/usr/bin/env python

# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

import unittest

from dathomir import resource

class TestResource(resource.TemplateResource):
	def get_paths(self):
		return ['/test']
	
	def prepare_content(self, req):
		self.set_slot('test', 'This is my test string.')
		self.set_slot('one', 1)
		self.set_slot('two', 2)
	
	def get_template(self, req):
		return 'The string is "$test", one is $one, two is $two'

class TemplateResourceTestCase(unittest.TestCase):
	def test_one(self):
		res = TestResource()
		res.prepare_content(None)
		self.assertEqual(res.get_content(None), 'The string is "This is my test string.", one is 1, two is 2')

if __name__ == "__main__":
	unittest.main()
