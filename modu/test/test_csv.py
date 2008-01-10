# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from twisted.trial import unittest

from modu.util import csv

simplest = 'one,two,three,four'
simpler = 'one,two,three,"last one"'
simple = 'one,"two with "" here",three,four'

tricky = 'one,"two with end """,three,four'

hard = 'one,two,three,"four\nwith return",five'
harder = 'one,"two\nwith return\nand "" quotes",three,four'
hardest = 'one,"two\nwith return\nand """""" quotes",three,four'

tabs = 'one\ttwo\tthree\tfour'
tabs_quoted = 'one\t"two here"\tthree\tfour'
tabs_oo = '"#1234"	something else here	"another quoted string"	1234'

class CSVTestCase(unittest.TestCase):
	def test_simplest(self):
		expected = ['one', 'two', 'three', 'four']
		got = csv.parse_line(simplest)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_simplest_columns(self):
		cols = ['one', 'two', 'three', 'four']
		expected = dict(one='one', two='two', three='three', four='four')
		got = csv.parse_line(simplest, column_names=cols)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
		for k, v in got.items():
			self.failUnlessEqual(k, v, 'column names were improperly assigned')
	
	def test_simpler(self):
		expected = ['one', 'two', 'three', 'last one']
		got = csv.parse_line(simpler)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_simple(self):
		expected = ['one', 'two with " here', 'three', 'four']
		got = csv.parse_line(simple)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_tricky(self):
		expected = ['one', 'two with end "', 'three', 'four']
		got = csv.parse_line(tricky)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_hard(self):
		expected = ['one', 'two', 'three', 'four\nwith return', 'five']
		got = csv.parse_line(hard)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_harder(self):
		expected = ['one', 'two\nwith return\nand " quotes', 'three', 'four']
		got = csv.parse_line(harder)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_hardest(self):
		expected = ['one', 'two\nwith return\nand """ quotes', 'three', 'four']
		got = csv.parse_line(hardest)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_tabs(self):
		expected = ['one', 'two', 'three', 'four']
		got = csv.parse_line(tabs, separator='\t')
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_tabs_quoted(self):
		expected = ['one', 'two here', 'three', 'four']
		got = csv.parse_line(tabs_quoted, separator='\t')
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_tabs_oo(self):
		expected = ['#1234', 'something else here', 'another quoted string', '1234']
		got = csv.parse_line(tabs_oo, separator='\t')
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
