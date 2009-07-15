# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

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
			verified_urlcode = model.create_url_code(phrase, storable.get_table(), req.store.pool,
				check_field='url_code', user_defined=existing_url_code, origin_id=storable.get_id())
		except ValueError, e:
			form[destination_field](value=str(e))
			form.set_error(destination_field, 'The url code entered has been adjusted. Hit save again to use the corrected code.')
			return False
		
		setattr(storable, destination_field, verified_urlcode)
		form[destination_field](value=verified_urlcode)
		
		return True
	return _generator