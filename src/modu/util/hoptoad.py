# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#
# See LICENSE for details

"""
Support for the HopToad error tracking service.
"""

import httplib, urllib2, re

from modu.util.url import urlparse

from arm import site 

RE_TRACEBACK_FILE = re.compile(r'\s*File "(?P<file>[^"]+)", line (?P<number>\d+), in (?P<method>\w+)')

def error_handler(req, failure):
	err = create_xml_submission(req, failure)
	submit_xml_error(req, err)

def create_yaml_submission(req, failure):
	from yaml import load, dump
	try:
		from yaml import CLoader as Loader
		from yaml import CDumper as Dumper
	except ImportError:
		from yaml import Loader, Dumper
	
	backtrace = failure.getTraceback().split('\n')
	backtrace.insert(0, backtrace[-4])
	data = dict(notice  = dict(
		api_key			= req.app.hoptoad_api_key,
		session			= dict(
			key			= req.session.id(),
			data		= req.session.copy(),
		),
		error_message	= "%s: %s" % (failure.type.__name__, str(failure.value)),
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

def submit_yaml_error(req, error_report):
	headers = { 'Content-Type': 'application/x-yaml', 
				'Accept': 'text/xml, application/xml', }
	r = urllib2.Request('http://hoptoadapp.com/notices', error_report, headers)
	try:
		urllib2.urlopen(r)
	except urllib2.URLError:
		req.log_error("Couldn't report traceback due to error: %s" % s)

def create_xml_submission(req, failure):
	from xml import dom
	
	impl = dom.getDOMImplementation()
	doc = impl.createDocument('http://hoptoadapp.com/hoptoad_2_0.xsd', 'notice', None)
	notice = doc.documentElement
	
	def create(name, *content, **attribs):
		e = doc.createElement(name)
		for k, v in attribs.items():
			e.setAttribute(k, v)
		for child in content:
			if(isinstance(child, basestring)):
				child = doc.createTextNode(child)
			e.appendChild(child)
		return e
	
	backtrace = create('backtrace')
	backtrace_lines = failure.getTraceback().split('\n')
	
	last_line_info = None
	for index in range(len(backtrace_lines)):
		line = backtrace_lines[index]
		match = RE_TRACEBACK_FILE.match(line)
		if(match):
			last_line_info = match.groupdict()
			backtrace.insertBefore(create('line', **last_line_info), backtrace.firstChild)
	
	query = {}
	if(req['QUERY_STRING']):
		query = req.data.copy()
	
	notice.setAttribute('version', '2.0.0')
	notice.appendChild(create('api-key', req.app.hoptoad_api_key))
	
	notifier = create('notifier')
	notifier.appendChild(create('name', 'modu hoptoad notifier'))
	notifier.appendChild(create('version', '$Id$'))
	notifier.appendChild(create('url', 'http://modu.bubblehouse.org/trac/browser/trunk/modu/util/hoptoad.py'))
	notice.appendChild(notifier)
	
	error = create('error')
	error.appendChild(create('class', failure.type.__name__))
	error.appendChild(create('message', str(failure.value)))
	error.appendChild(backtrace)
	notice.appendChild(error)
	
	request = create('request')
	request.appendChild(create('url', req.get_path(req.path, **query)))
	request.appendChild(create('component', last_line_info.get('file')))
	request.appendChild(create('action', last_line_info.get('method')))
	
	if(req.data):
		params = create('params')
		for k, v in req.data.copy().items():
			params.appendChild(create('var', str(v), key=k))
		request.appendChild(params)
	
	if(req.session):
		session = create('session')
		for k, v in req.session.copy().items():
			session.appendChild(create('var', str(v), key=k))
		request.appendChild(session)
	
	cgi_data = create('cgi-data')
	for k, v in req.simplify().items():
		cgi_data.appendChild(create('var', str(v), key=k))
	request.appendChild(cgi_data)
	
	notice.appendChild(request)
	
	server_environment = create('server-environment')
	server_environment.appendChild(create('project-root', req.approot))
	server_environment.appendChild(create('environment-name', site.current_hostname))
	notice.appendChild(server_environment)
	
	return notice.toxml()

def submit_xml_error(req, error_report):
	headers = { 'Content-Type': 'text/xml', 
				'Accept': 'text/xml, application/xml', }
	r = urllib2.Request('http://arm.hoptoadapp.com/notifier_api/v2/notices', error_report, headers)
	try:
		urllib2.urlopen(r)
	except urllib2.URLError, e:
		req.log_error("Couldn't report traceback due to error: %s" % s)


