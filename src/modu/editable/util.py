# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

import re

from modu.persist import sql

def get_url_code_callback(source_field, destination_field):
	"""
	Auto-generate URL codes and give opportunity for approval.
	
	Used in any interface that requires a URL code
	"""
	def _generator(req, form, storable):
		"""
		Take 'phrase' and replace ranges of non-alphanumerics with
		dashes. Check if it exists in `table.column` through the
		provided connection.
		"""
		# First, try using the user-defined url code, if available
		existing_url_code = req.data[form.name][destination_field].value
		
		# Then, grab the phrase we'll use as source material
		phrase = req.data[form.name][source_field].value
		# If it's not there (e.g., not in the admin form), grab it from the object
		if(phrase == ''):
			phrase = getattr(storable, source_field, '')
		
		pool = storable.get_store().pool
		
		try:
			verified_urlcode = create_url_code(phrase, storable.get_table(), req.store.pool,
				check_field='url_code', user_defined=existing_url_code, origin_id=storable.get_id())
		except ValueError, e:
			form[destination_field](value=str(e))
			form.set_error(destination_field, 'The url code entered has been adjusted. Hit save again to use the corrected code.')
			return False
		
		setattr(storable, destination_field, verified_urlcode)
		form[destination_field](value=verified_urlcode)
		
		return True
	return _generator

def create_url_code(phrase, table, pool, check_field='url_code', user_defined=None, origin_id=None):
	def _make_code(text):
		urlcode = re.sub(r'\W+', '-', text.lower())
		return re.sub(r'^\-*(.*?)\-*$', lambda(m): m.group(1), urlcode)
	
	# Create a default url code
	urlcode = _make_code(phrase)
	
	# If the user has supplied a code...
	if(user_defined):
		# And it isn't a valid url code
		if(_make_code(user_defined) != user_defined):
			# we've already failed once
			attempt = 2
		# Otherwise...
		else:
			# Check the given code
			attempt = 1
			urlcode = user_defined
	# Otherwise, stay as is
	else:
		attempt = 1
	
	def _check_code(urlcode):
		if not(origin_id):
			attribs = {
				check_field:			urlcode
			}
		else:
			attribs = {
				'id':					sql.NOT(origin_id),
				check_field:			urlcode
			}
		return pool.runQuery(sql.build_select(table, attribs))
	
	verified_urlcode = urlcode
	
	results = _check_code(verified_urlcode)
	while(results):
		attempt += 1
		verified_urlcode = '%s-%d' % (urlcode, attempt)
		results = _check_code(verified_urlcode)
	
	if(user_defined is not None and attempt > 1 and user_defined != verified_urlcode):
		raise ValueError(verified_urlcode)
	
	return verified_urlcode

