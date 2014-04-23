# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
An example itemdef that contains all available options and field types.
"""

from modu.util import theme
from modu.editable import define
from modu.editable.datatypes import string, relational, boolean, select
from modu.persist import storable, sql

def pre_post_write_callback(req, form, storable):
	"""
	Called before or after the primary write.
	"""
	return True

def pre_post_delete_callback(req, form, storable):
	"""
	Called before or after an item is deleted.
	
	The return value from a postdelete callback has no effect.
	"""
	return True

def template_variable_callback(req, form, storable):
	"""
	Returns a dictionary to populate the template with.
	
	On a listing page, form will actually be an array of forms.
	"""
	return {}

def validator(req, frm, storable):
	return True

def fwhere_callback(storable):
	pass

def autocomplete_callback(req, partial, definition):
	output = ''
	for result in []: # do some query here
		output += "%s|%d\n" % (result['name'], result['id'])
	return output

def form_alter_callback(req, style, form, storable, definition):
	pass

def export_query_builder(req, itemdef, attribs):
	return sql.build_select(itemdef.name, attribs)

def export_formatter(req, itemdef, item):
	# Use m.u.OrderedDict to enforce column order
	return dict()

def export_callback(req):
	pass

# Itemdefs can be bound to any variable name, but they must be assigned to **something**
__itemdef__ = define.itemdef(
	# The configuration dict
	__config		= dict(
		# [r] A unique identifier for this itemdef, usually the table name
		name		= 'page',
		
		# [o] If the identifier is not the table name, it must be set here
		table		= '[default:<name>]',
		
		# [o] The display name of this itemdef
		label		= '[default:<name>]',
		
		# [o] The itemdef category
		category	= "[default:'other']",
		
		# [o] The position of this itemdef in relation to others in its category
		weight		= 5,
		
		# [o] The required user permission to use this itemdef
		acl			= '[default:'']',
		
		# [o] Alternate usage specifying multiple required permissions
		acl			= ['access pages',
		 				'access admin'],
		
		# [o] This is called during validation. If it returns false,
		#     validation will fail.
		prewrite_callback	= pre_post_write_callback,
		
		# [o] Called during submit, after writing the storable.
		postwrite_callback	= pre_post_write_callback,
		
		# [o] This is called during validation. If it returns false,
		#     validation will fail.
		predelete_callback	= pre_post_delete_callback,
		
		# [o] Called during submit, after writing the storable.
		postdelete_callback	= pre_post_delete_callback,
		
		# [o] Overrides the default theme class for form generation.
		theme				= theme.Theme,
		
		# [o] Factory to use to build Storable objects
		factory				= storable.DefaultFactory,
		
		# [o] Model class to use with DefaultFactory
		model_class			= storable.Storable,
		
		# [o] Overrides the default list template.
		list_template		= "[default:'admin-listing.tmpl.html']",
		
		# [o] Overrides the default detail template.
		detail_template		= "[default:'admin-detail.tmpl.html']",
		
		# [o] A dict of name-value pairs returned from this function
		#     will be added to the template
		template_variable_callback = template_variable_callback,
		
		# [o] The name of a result column that should be used as the title
		#     of a record
		title_column		= 'title',
		
		# [o] Don't allow anyone to create a new item.
		no_create			= False,
		
		# [o] The number of results to show per listing page.
		per_page			= 25,
		
		# [o] The title to be displayed on listing pages.
		listing_title		= "[default:'Listing <Name> Records']",
		
		# [o] When using the export feature, this function will be called to generate the query
		export_query_builder = export_query_builder
		
		# [o] Export type (may be 'csv' or 'tsv'
		export_type 		= 'csv',
		
		# [o] Line endings to use in exported CSV
		export_le 			= '\n',
		
		# [o] When using the export feature, this function will be called to generate the query
		export_formatter = export_formatter,
		
		# [o] When using the export feature, this function will be called to generate the query
		export_callback = export_callback,
		
		# [o] If `resource` is defined, this resource will provide the content for this 
		#     itemdef while most other itemdef configuration variables (and any defined
		#     fields) will be ignored.
		resource		= None,
		
		# [o] TODO: Alternate usage
		# acl			= {'view':'view pages',
		#  				'edit':'edit pages'},
	),
	
	# The name of a field is automatically set by the parent itemdef, so it doesn't
	# appear in the definition constructor
	# the attributes of this example field are available on all fields
	# Normally you wouldn't ever instantiate define.definition
	example			= define.definition(
		# [o] The column in the result for this field.
		column		= '[default:field-name]',
		
		# [o] The label to appear on this form item
		label		= '[default:field-name]',
		
		# [o] Help text for this field.
		help		= '[default:'']',
		
		# [o] Should this field appear in list view?
		listing		= False,
		
		# [o] If True, this field will have a hyperlink added as a
		#     form prefix/suffix that will link to the detail URL.
		link		= False,
		
		# [o] Should this field appear in detail view?
		detail		= True,
		
		# [o] If supported, this field should be uneditable/disabled
		read_only	= False,
		
		# [o] Should this field appear in the listing search form?
		search		= False,
		
		# [o] The weight (relative position) of this field
		weight		= 0,
		
		# [o] Attributes set here will define or override 
		#     values on the resulting FormNode instance.
		attributes	= {},
		
		# [o] After a form is generated, it will be passed to
		#     this function, if defined, which may modify the resulting
		#     form element.
		form_alter	= form_alter_callback,
		
		# [o] a function to validate this field's contents
		validator	= validator,
		
		# [o] If False, this field's contents will never be saved/updated
		implicit_save = True,
	),
	
	id					= string.LabelField(
		# [o] Should search on this field use MATCH() AGAINST()?
		#     This overrides an `exact_match` setting if both are present.
		fulltext_search	= False
		# [o] Should search on this field use equals?
		exact_match		= False
	),
	
	active				= boolean.CheckboxField(
		# [o] The value saved to the DB field when checked
		checked_value	=	1,
		
		# [o] The value saved to the DB field when unchecked
		unchecked_value	=	0
	),
	
	title				= string.StringField(
		# [o] the textfield displayed size
		size			= 30,
		
		# [o] the max number of chars, if defined
		maxlength 		= None,
		
		# [o] Should search on this field use MATCH() AGAINST()?
		#     This overrides an `exact_match` setting if both are present.
		fulltext_search	= False
		
		# [o] Should search on this field use equals?
		exact_match		= False
	),
	
	body				= string.TextAreaField(
		# [o] the number of displayed columns
		cols			= 40,
		
		# [o] the number of displayed columns rows
		rows			= 5,
		
		# [o] Should search on this field use MATCH() AGAINST()?
		#     This overrides an `exact_match` setting if both are present.
		fulltext_search	= False
		
		# [o] Should search on this field use equals?
		exact_match		= False
	),
	
	htmlbody			= fck.FCKEditorField(
		# [o] Should search on this field use MATCH() AGAINST()?
		fulltext_search	= False,
		# [o] The path where FCKEditorResource was registered.
		fck_root		= '/fck'
		# [o] The width of the FCKEditor in pixels
		width			= 600,
		# [o] The height of the FCKEditor in pixels
		heght			= 400,
		# [o] The toolbar set to use, as defined in the FCK config
		toolbar_set		= 'Standard'
	),
	
	password			= string.PasswordField(
		# [o] Should this field be protected from view?
		obfuscate		= True,
		
		# [o] Should this field use ENCRYPT() when saving?
		encrypt			= True,
		
		# [o] Should a second field be displayed for verification?
		verify			= True
	),
	 
	type				= select.SelectField(
		# [r] The available options for this field. If a dict, the
		#     **keys** are saved to the database. If a sequence, the
		#     **indices** are saved.
		options			= True
	),
	 
	created_date		= date.DateField(
		# [o] When printed in list or read-only views, use this format string.
		format_string	= '%B %d, %Y at %I:%M%p',
		
		# [o] Starting year for year select field
		start_year		= '[default: this year - 2]',
		
		# [o] Ending year for year select field
		end_year		= '[default: this year + 5]'
		
		# [o] If True, when this field is NULL (or is a part of new record), 
		#     pre-set the date selector to the current date/time.
		default_now		= False,
		
		# [o] Is this a date, datetime, or time field?
		style			= 'datetime',
		
		# [o] Should the field value be saved as a timestamp (int(11)),
		#     or date/datetime/time object (date, datetime, or time columns)
		save_format		= 'timestamp'
	),
	 
	creator_id			= relational.ForeignLabelField(
		# [r] The name of the foreign table
		ftable			= 'user',
		
		# [r] The name of the value field in the foreign table
		fvalue			= 'id',
		
		# [r] The name of the foreign field to display as a label
		flabel			= 'username'
	),
	
	category_id			= relational.ForeignSelectField(
		# [r] The name of the foreign table
		ftable			= 'category',
		
		# [r] The name of the value field in the foreign table
		fvalue			= 'id',
		
		# [r] The name of the foreign field to display as a label
		flabel			= 'name',
		
		# [o] A string specifying the WHERE clause, OR
		fwhere			= 'WHERE active = 1',
		
		# [o] An array to use to build the WHERE clause, OR
		# fwhere			= {'active':1},
		
		# [o] A callable that returns either a string or a dict
		# fwhere			= fwhere_callback
	),
	 
	topic_id			= relational.ForeignAutocompleteField(
		# [r] The name of the foreign table
		ftable			= 'topic',
		
		# [r] The name of the value field in the foreign table
		fvalue			= 'id',
		
		# [r] The name of the foreign field to display as a label
		flabel			= 'name',
		
		# [o] A string specifying the WHERE clause, OR
		fwhere			= "[default:'']",
		
		# [o] An array to use to build the WHERE clause, OR
		# fwhere			= {'active':1},
		
		# [o] A callable that returns either a string or a dict
		# fwhere			= fwhere_callback
		
		# [o] The number of chars that must be typed to start a lokup
		min_chars		= 3,
		
		# [o] The number of matches to display
		max_choices		= 10,
		
		# [r] Use this function to generate autocomplete results
		autocomplete_callback = autocomplete_callback
	),
	
	# In foreign multiple field (e.g., n2m relationships), the m table is considered the
	# 'foreign table', and this itemdef's table the 'n' table, hence the prefix 'f' and 'n'
	other_categories	= relational.ForeignMultipleSelectField(
		# [r] The name of the foreign table
		ftable			= 'category',
		
		# [o] The name of the value field in the foreign table
		fvalue			= 'id',
		
		# [r] The name of the foreign field to display as a label
		flabel			= 'title',
		
		# [o] A string specifying the WHERE clause, OR
		fwhere			= "[default:'']",
		
		# [o] An array to use to build the WHERE clause, OR
		# fwhere			= {'active':1},
		
		# [o] A callable that returns either a string or a dict
		# fwhere			= fwhere_callback
		
		# [r] The name of the n2m table
		ntof			= 'page_category',
		
		# [r] The name of the foreign table's id column in the
		#     n2m table (where fvalue is saved)
		ntof_f_id		= 'category_id',
		
		# [r] The name of this itemdef's table's id column in
		#     the n2m table
		ntof_n_id		= 'page_id'
	),

	other_topics		= relational.ForeignMultipleAutocompleteField(
		# [r] The name of the foreign table
		ftable			= 'category',
		
		# [o] The name of the value field in the foreign table
		fvalue			= 'id',
		
		# [r] The name of the foreign field to display as a label
		flabel			= 'title',
		
		# [o] A string specifying the WHERE clause, OR
		fwhere			= "[default:'']",
		
		# [o] An array to use to build the WHERE clause, OR
		# fwhere			= {'active':1},
		
		# [o] A callable that returns either a string or a dict
		# fwhere			= fwhere_callback
		
		# [r] The name of the n2m table
		ntof			= 'page_category',
		
		# [r] The name of the foreign table's id column in the
		#     n2m table (where fvalue is saved)
		ntof_f_id		= 'category_id',
		
		# [r] The name of this itemdef's table's id column in
		#     the n2m table
		ntof_n_id		= 'page_id',
		
		# [o] The number of chars that must be typed to start a lokup
		min_chars		= 3,
		
		# [o] The number of matches to display
		max_choices		= 10,
		
		# [r] Use this function to generate autocomplete results
		autocomplete_callback = autocomplete_callback
	)
)