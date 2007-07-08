# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

from modu.persist import storable
from modu.sabi import api

class SabiFactory(storable.DefaultFactory):
	def __init__(self, req, table=None, model_class=None):
		self.req = req
		self.table = table
		self.model_class = model_class
	
	def create_item(self, data):
		item = super(SabiFactory, self).create_item(data)
		api.invoke('load', self.table, item)
	
	def create_item_query(self, data):
		pass
	
	def create_item_query_for_table(self, table, data):
		pass
	
	def get_item(self, id):
		pass
	
	def get_items(self, data):
		pass
	
	def get_items_by_query(self, query):
		pass
	
	def get_item_records(self, query):
		pass
