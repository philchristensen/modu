# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

import unittest, socket, urllib

from modu.web import resource, user

TEST_TABLES = """
DROP TABLE IF EXISTS `page`;
CREATE TABLE IF NOT EXISTS `page` (
  `id` bigint(20) unsigned NOT NULL default 0,
  `code` varchar(128) NOT NULL default '',
  `password` varchar(255) NOT NULL default '',
  `category_id` int(11) NOT NULL default 0,
  `content` text NOT NULL,
  `title` varchar(64) NOT NULL default '',
  `created_date` int(11) NOT NULL default '0',
  `modified_date` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `subpage`;
CREATE TABLE IF NOT EXISTS `subpage` (
  `id` bigint(20) unsigned NOT NULL default 0,
  `code` varchar(128) NOT NULL default '',
  `password` varchar(255) NOT NULL default '',
  `category_id` int(11) NOT NULL default 0,
  `content` text NOT NULL,
  `title` varchar(64) NOT NULL default '',
  `created_date` int(11) NOT NULL default '0',
  `modified_date` int(11) NOT NULL default '0',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `category`;
CREATE TABLE IF NOT EXISTS `category` (
  `id` bigint(20) unsigned NOT NULL default 0,
  `code` varchar(255) NOT NULL default '',
  `title` varchar(255) NOT NULL default '',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `code_uni` (`code`)
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `category` (id, code, title) VALUES
(1, 'drama', 'Drama'), (2, 'sci-fi', 'Science Fiction'),
(3, 'bio', 'Biography'), (4, 'horror', 'Horror'),
(5, 'science', 'Science'), (6, 'historical-fiction', 'Historical Fiction'),
(7, 'self-help', 'Self-Help'), (8, 'romance', 'Romance'),
(9, 'business', 'Business'), (10, 'technical', 'Technical'),
(11, 'engineering', 'Engineering'), (12, 'language', 'Lanugage'),
(13, 'finance', 'Finance'), (14, 'young-readers', 'Young Readers'),
(15, 'music', 'Music'), (16, 'dance', 'Dance'),
(17, 'psychology', 'Psychology'), (18, 'astronomy', 'Astronomy'),
(19, 'physics', 'Physics'), (20, 'politics', 'Politics');

DROP TABLE IF EXISTS `page_category`;
CREATE TABLE IF NOT EXISTS `page_category` (
  `page_id` bigint(20) unsigned NOT NULL,
  `category_id` bigint(20) unsigned NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `guid`;
CREATE TABLE IF NOT EXISTS `guid` (
  `guid` bigint(20) unsigned NOT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

INSERT INTO `guid` VALUES (5);
"""

"""
CREATE DATABASE modu;
GRANT ALL ON modu.* TO modu@localhost IDENTIFIED BY 'modu';
"""

def generate_test_wsgi_environment(post_data={}, multipart=True):
	"""
	Set REQUEST_URI
	Set SCRIPT_NAME to app.base_path
	"""
	environ = {}
	environ['wsgi.errors'] = StringIO.StringIO()
	environ['wsgi.file_wrapper'] = file

	input_data = StringIO.StringIO()
	if(post_data):
		if(multipart):
			for name,value in post_data:
				input_data.write("------TestingFormBoundaryJe0Hll5QdEhCQiZj\n")
				input_data.write("Content-Disposition: form-data; name=\"%s\"\n\n" % name)
				input_data.write("%s\n" % value)
			input_data.write("------TestingFormBoundaryJe0Hll5QdEhCQiZj--\n")
			environ['CONTENT_TYPE'] = 'multipart/form-data; boundary=----TestingFormBoundaryJe0Hll5QdEhCQiZj'
		else:
			input_data.write(urllib.urlencode(post_data))
			environ['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'
		environ['CONTENT_LENGTH'] = input_data.tell()
		input_data.seek(0)
		environ['REQUEST_METHOD'] = 'POST'
	else:
		environ['REQUEST_METHOD'] = 'GET'
	
	environ['wsgi.input'] = input_data
	
	environ['GATEWAY_INTERFACE'] = 'CGI/1.1'
	environ['HTTPS'] = 'off'
	environ['HTTP_ACCEPT'] = 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5'
	environ['HTTP_ACCEPT_ENCODING'] = 'gzip, deflate'
	environ['HTTP_ACCEPT_LANGUAGE'] = 'en'
	environ['HTTP_CONNECTION'] = 'keep-alive'
	environ['HTTP_HOST'] = 'localhost:8888'
	environ['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en) AppleWebKit/522.11.1 (KHTML, like Gecko) Version/3.0.3 Safari/522.12.1'
	environ['QUERY_STRING'] = ''
	environ['REMOTE_ADDR'] = '127.0.0.1'
	environ['REMOTE_HOST'] = socket.gethostname()
	environ['REMOTE_PORT'] = '56546'
	environ['REQUEST_SCHEME'] = 'http'
	environ['wsgi.url_scheme'] = 'http'
	environ['SCRIPT_NAME'] = ''
	environ['SERVER_NAME'] = 'localhost'
	environ['SERVER_PORT'] = '8888'
	environ['SERVER_PORT_SECURE'] = '0'
	environ['SERVER_PROTOCOL'] = 'HTTP/1.1'
	environ['SERVER_SOFTWARE'] = 'TwistedWeb/2.5.0+rUnknown'
	environ['wsgi.multiprocess'] = 'False'
	environ['wsgi.multithread'] = 'True'
	environ['wsgi.run_once'] = 'False'
	environ['wsgi.url_scheme'] = 'http'
	environ['wsgi.version'] = '(1, 0)'
	
	return environ

class TestAdminUser(user.User):
	def is_allowed(self, permission):
		return True
	
	def has_role(self, role):
		return False
	
	def get_data(self):
		raise RuntimeError('It is not possible to save the test admin user object.')
	
	def get_id(self):
		return 0
	
	def set_id(self):
		raise RuntimeError('It is not possible to set the ID of the test admin user object.')

