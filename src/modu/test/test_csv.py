# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

try:
	import cStringIO as StringIO
except ImportError, e:
	import StringIO

from twisted.trial import unittest

from modu.util import csv

simplest = 'one,two,three,four'
simpler = 'one,two,three,"last one"'
simple = 'one,"two with "" here",three,four'

tricky = 'one,"two with end """,three,four'

hard = 'one,two,three,"four\nwith return",five'
harder = 'one,"two\nwith return\nand "" quotes",three,four'
hardest = 'one,"two\nwith return\nand """""" quotes",three,four'

tabs = 'one\ttwo\t\tthree\tfour'
tabs_quoted = 'one\t"two here"\tthree\tfour'
tabs_oo = '"#1234"	something else here	"another quoted string"	1234'

known_bad_1 = '"LCD1066"\t"Take Your Time"\t\t\t"LCD1066-4"\t"Letter From Home, The Harmonic Branching"\t"9m34s"\t"Lovely Music"\t"Tyranny, ""Blue"" Gene"\t"Tyranny, ""Blue"" Gene (piano)"\t\t\t\t\t\t\t\t\t\t'

multiline = '"one","two","three"%s"one","two","three"%s"one","two","three"%s"one","two","three"%s"one","two","three"'

class CSVTestCase(unittest.TestCase):
	def test_multiline_r(self):
		io = StringIO.StringIO(multiline % ('\r', '\r', '\r', '\r'))
		expected = [['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three']]
		got = csv.parse(io)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_multiline_rn(self):
		io = StringIO.StringIO(multiline % ('\r\n', '\r\n', '\r\n', '\r\n'))
		expected = [['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three']]
		got = csv.parse(io)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_multiline_n(self):
		io = StringIO.StringIO(multiline % ('\n', '\n', '\n', '\n'))
		expected = [['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three']]
		got = csv.parse(io)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_multiline_nr(self):
		io = StringIO.StringIO(multiline % ('\n\r', '\n\r', '\n\r', '\n\r'))
		expected = [['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three'], ['one', 'two', 'three']]
		got = csv.parse(io)
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
	def test_known_bad_1(self):
		expected = ['LCD1066', 'Take Your Time', '', '', 'LCD1066-4', 'Letter From Home, The Harmonic Branching', '9m34s', 'Lovely Music', 'Tyranny, "Blue" Gene', 'Tyranny, "Blue" Gene (piano)', '', '', '', '', '', '', '', '', '']
		got = csv.parse_line(known_bad_1, separator="\t")
		self.failUnlessEqual(got, expected, 'Got %s when expecting %s' % (got, expected))
	
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
		expected = ['one', 'two', '', 'three', 'four']
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
	
