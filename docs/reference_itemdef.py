# modu
# Copyright (C) 2007-2008 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
An example itemdef that contains all available options and field types.
"""

from modu.util import theme
from modu.editable import define
from modu.editable.datatypes import string, relational, boolean, select
from modu.persist import storable

def noop(req, form, storable):
	"""
	A dummy function.
	"""
	pass

def fwhere_callback(storable):
	pass

def autocomplete_callback(req, partial, definition):
	output = ''
	for result in []: # do some query here
		output += "%s|%d\n" % (result['name'], result['id'])
	return output

def form_alter_callback(req, style, form, storable, definition):
	pass

# Itemdefs can be bound to any variable name, but they must be assigned to **something**
__itemdef__ = define.itemdef(
	# The configuration dict
	__config		= dict(
		name		= 'page',					# [r] A unique identifier for this itemdef, usually the table name
		table		= '[default:<name>]',		# [o] If the identifier is not the table name, it must be set here
		label		= '[default:<name>]',		# [o] The display name of this itemdef
		category	= "[default:'other']",		# [o] The itemdef category
		weight		= 5,						# [o] The position of this itemdef in relation to others in its category
		acl			= '[default:'']',			# [o] The required user permission to use this itemdef
		# acl			= ['access pages',		# Alternate usage specifying multiple required permissions
		# 				'access admin'],
		# TODO:
		# acl			= {'view':'view pages',	# Alternate usage
		#  				'edit':'edit pages'}
		prewrite_callback	= noop,				# [o] This is called during validation. If it returns false,
												# validation will fail.
		postwrite_callback	= noop,				# [o] Called during submit, after writing the storable.
		theme				= theme.Theme,		# [o] Overrides the default theme class for form generation.
		factory				= storable.DefaultFactory,		# [o] Factory to use to build Storable objects
		model_class			= storable.Storable,			# [o] Model class to use with DefaultFactory
		list_template		= "[default:'admin-listing.tmpl.html']",	# [o] Overrides the default list template.
		detail_template		= "[default:'admin-detail.tmpl.html']",		# [o] Overrides the default detail template.
		template_variable_callback = noop		# [o] A dict of name-value pairs returned from this function
												# will be added to the template
	),
	
	# The name of a field is automatically set by the parent itemdef, so it doesn't
	# appear in the definition constructor
	# the attributes of this example field are available on all fields
	example			= define.definition(		# Normally you wouldn't ever instantiate this
		label		= '[default:field-name]',	# [o] The label to appear on this form item
		help		= '[default:'']',			# [o] Help text (tooltip) for this field.
		listing		= False,					# [o] Should this field appear in list view?
		link		= False,					# [o] If True, this field will have a hyperlink added as a
												# form prefix/suffix that will link to the detail URL.
		detail		= True,						# [o] Should this field appear in detail view?
		read_only	= False,					# [o] If supported, this field should be uneditable/disabled
		search		= False,					# [o] Should this field appear in the listing search form?
		weight		= 0,						# [o] The weight (relative position) of this field
		attributes	= {},						# [o] Attributes set here will define or override 
												# values on the resulting FormNode instance.
		form_alter	= form_alter_callback		# [o] After a form is generated, it will be passed to
												# this function, if defined, which may modify the resulting
												# form element.
	),
	
	id					= string.LabelField(
		fulltext_search	= False					# [o] Should search on this field use MATCH() AGAINST()?
	),
	
	active				= boolean.CheckboxField(
		checked_value	=	1,					# [o] The value saved to the DB field when checked
		unchecked_value	=	0					# [o] The value saved to the DB field when unchecked
	),
	
	title				= string.StringField(
		size			= 30,					# [o] the textfield displayed size
		maxlength 		= None,					# [o] the max number of chars, if defined
		fulltext_search	= False					# [o] Should search on this field use MATCH() AGAINST()?
	),
	
	body				= string.TextAreaField(
		cols			= 40,					# [o] the number of displayed columns
		rows			= 5,					# [o] the number of displayed columns rows
		fulltext_search	= False					# [o] Should search on this field use MATCH() AGAINST()?
	),
	
	password			= string.PasswordField(
		obfuscate		= True,					# [o] Should this field be protected from view?
		encrypt			= True,					# [o] Should this field use ENCRYPT() when saving?
		verify			= True					# [o] Should a second field be displayed for verification?
	),
	 
	type				= select.SelectField(
		options			= True					# [r] The available options for this field. If a dict, the
												# **keys** are saved to the database. If a sequence, the
												# **indices** are saved.
	),
	 
	creator_id			= relational.ForeignLabelField(
		ftable			= 'user',				# [r] The name of the foreign table
		fvalue			= 'id',					# [r] The name of the value field in the foreign table
		flabel			= 'username'			# [r] The name of the foreign field to display as a label
	),
	
	category_id			= relational.ForeignSelectField(
		ftable			= 'category',			# [r] The name of the foreign table
		fvalue			= 'id',					# [r] The name of the value field in the foreign table
		flabel			= 'name',				# [r] The name of the foreign field to display as a label
		fwhere			= 'WHERE active = 1',	# [o] A string specifying the WHERE clause, OR
		# fwhere			= {'active':1},		# [o] An array to use to build the WHERE clause, OR
		# fwhere			= fwhere_callback	# [o] A callable that returns either a string or a dict
	),
	 
	topic_id			= relational.ForeignAutocompleteField(
		ftable			= 'topic',						# [r] The name of the foreign table
		fvalue			= 'id',							# [r] The name of the value field in the foreign table
		flabel			= 'name',						# [r] The name of the foreign field to display as a label
		fwhere			= "[default:'']",				# [o] A string specifying the WHERE clause, OR
		# fwhere			= {'active':1},				# [o] An array to use to build the WHERE clause, OR
		# fwhere			= fwhere_callback			# [o] A callable that returns either a string or a dict
		min_chars		= 3,							# [o] The number of chars that must be typed to start a lokup
		max_choices		= 10,							# [o] The number of matches to display
		autocomplete_callback = autocomplete_callback	# [r] Use this function to generate autocomplete results
	),
	
	# In foreign multiple field (e.g., n2m relationships), the m table is considered the
	# 'foreign table', and this itemdef's table the 'n' table, hence the prefix 'f' and 'n'
	other_categories	= relational.ForeignMultipleSelectField(
		ftable			= 'category',			# [r] The name of the foreign table
		fvalue			= 'id',					# [o] The name of the value field in the foreign table
		flabel			= 'title',				# [r] The name of the foreign field to display as a label
		fwhere			= "[default:'']",		# [o] A string specifying the WHERE clause, OR
		# fwhere			= {'active':1},		# [o] An array to use to build the WHERE clause, OR
		# fwhere			= fwhere_callback	# [o] A callable that returns either a string or a dict
		ntof			= 'page_category',		# [r] The name of the n2m table
		ntof_f_id		= 'category_id',		# [r] The name of the foreign table's id column in the
												# n2m table (where fvalue is saved)
		ntof_n_id		= 'page_id'				# [r] The name of this itemdef's table's id column in
												# the n2m table
	),

	other_topics		= relational.ForeignMultipleAutocompleteField(
		ftable			= 'category',					# [r] The name of the foreign table
		fvalue			= 'id',							# [o] The name of the value field in the foreign table
		flabel			= 'title',						# [r] The name of the foreign field to display as a label
		fwhere			= "[default:'']",				# [o] A string specifying the WHERE clause, OR
		# fwhere			= {'active':1},				# [o] An array to use to build the WHERE clause, OR
		# fwhere			= fwhere_callback			# [o] A callable that returns either a string or a dict
		ntof			= 'page_category',				# [r] The name of the n2m table
		ntof_f_id		= 'category_id',				# [r] The name of the foreign table's id column in the
														# n2m table (where fvalue is saved)
		ntof_n_id		= 'page_id',					# [r] The name of this itemdef's table's id column in
														# the n2m table
		min_chars		= 3,							# [o] The number of chars that must be typed to start a lokup
		max_choices		= 10,							# [o] The number of matches to display
		autocomplete_callback = autocomplete_callback	# [r] Use this function to generate autocomplete results
	)
)