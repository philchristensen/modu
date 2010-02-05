# modusite
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
# $Id$
#

import os, os.path

from modu.persist import storable

def get_checksum(filepath, md5_path='md5sum'):
	handle = os.popen(md5_path + ' "' + filepath.replace(r';', r'\;') + '"')
	filehash = handle.read()
	handle.close()
	
	if(filehash.find('=') == -1):
		filehash = [output.strip() for output in filehash.split(' ')][0]
	else:
		filehash = [output.strip() for output in filehash.split('=')][1]
	
	return filehash

class Release(storable.Storable):
	def __init__(self):
		super(Release, self).__init__('release')
	
	def load_tarball_info(self, req, filename):
		if(filename.endswith('.tar.gz')):
			full_path = os.path.join(req.app.release_path, filename)
			md5_path = req.app.config.get('md5_path', 'md5sum')
			if not(getattr(self, 'tarball_url', None)):
				self.filename = filename
				self.tarball_url = req.get_path('releases', filename)
				self.tarball_checksum = get_checksum(full_path, md5_path=md5_path)
		