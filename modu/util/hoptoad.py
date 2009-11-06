# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Support for the HopToad error tracking service.
"""

import httplib, urllib2

from yaml import load, dump
try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from modu.util.url import urlparse

def error_handler(req, failure):
	err = create_submission(req, failure)
	return submit_error(err)

def create_submission(req, failure):
	backtrace = failure.getTraceback().split('\n')
	backtrace.insert(0, backtrace[-4])
	data = dict(notice  = dict(
		api_key			= req.app.hoptoad_api_key,
		session			= dict(
			key			= req.session.id(),
			data		= req.session.copy(),
		),
		error_message	= str(failure.value),
		error_class		= failure.type.__name__,
		backtrace		= backtrace,
		request			= dict(
			rails_root	= req.approot,
			url			= req.get_path(req.path),
			params		= req.data.copy(),
		),
		environment		= req.simplify(),
	))
	result = dump(data, default_flow_style=False, Dumper=Dumper)
	
	return result

def submit_error(error_report):
	headers = { 'Content-Type': 'application/x-yaml', 
				'Accept': 'text/xml, application/xml', }
	r = urllib2.Request('http://hoptoadapp.com/notices', error_report, headers)
	status = urllib2.urlopen(r)
	return status

