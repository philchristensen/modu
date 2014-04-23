# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

import os, os.path, shutil, re, datetime

from modu.persist import Store, dbapi, sql
from modu.web import app

import modusite
from modusite.model import project, release
from modu.sites import modusite_site

RE_TARBALL_VERSION = re.compile(r'^(\w+?)-((?:\d\.)+\d.*)\.tar\.gz$', re.IGNORECASE)

def get_release_request(hostname):
	env = {
		'SERVER_NAME'		: hostname,
		'SERVER_PORT'		: '80',
		'PATH_INFO'			: '/',
		'SCRIPT_NAME' 		: '',
		'wsgi.url_scheme'	: 'https',
	}
	
	req = app.Request()
	application = app.get_application(env)
	if not(application):
		raise RuntimeError("Can't load application config.")
	
	application.make_immutable()
	req = app.configure_request(env, application)
	if(hasattr(application.site, 'configure_request')):
		application.site.configure_request(req)
	
	return req

def create(hostname, source, destination, nightly=False):
	os.chdir(source)
	os.system('svn update')
	
	existing = os.listdir(destination)
	
	os.system('python setup.py egg_info %s sdist' % (('-RDb ""', '')[int(nightly)]))
	
	filename = None
	for item in os.listdir(os.path.join(source, 'dist')):
		if(item not in existing):
			filename = item
			shutil.copy(os.path.join(source, 'dist', item), destination)
			break
	else:
		raise IOError("Tarball not found.")
	
	match = RE_TARBALL_VERSION.match(filename)
	if not(match):
		raise RuntimeError("Filename %s can't be parsed for project and version information." % filename)
	
	project_name = match.group(1)
	release_version = match.group(2)
	
	pool = dbapi.connect(modusite_site.db_url)
	store = Store(pool)
	
	store.ensure_factory('project', model_class=project.Project)
	store.ensure_factory('release', model_class=release.Release)
	
	p = store.load_one('project', shortname=project_name)
	if not(p):
		raise RuntimeError("No such project, '%s'" % project_name)
	
	r = store.load_one('release', project_id=p.get_id(), version_string=release_version)
	if(r):
		raise RuntimeError("There is already a '%s' release with version string '%s'" % (project_name, release_version))
	
	r = release.Release()
	r.project_id = p.get_id()
	r.active = 1
	r.nightly = int(nightly)
	r.release_date = datetime.datetime.now()
	
	r.license_name = p.license_name
	r.license_url = p.license_url
	r.installation_url = p.installation_url
	r.changelog_url = p.changelog_url

	r.version_string = release_version
	r.version_weight = re.sub(r'[-_.]', '', release_version)

	req = get_release_request(hostname)
	r.load_tarball_info(req, filename)
	
	store.save(r)
	