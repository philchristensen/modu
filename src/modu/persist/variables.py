# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
Persistent variables.

Somewhat modeled after Drupal variable system, this is a way for modu
developers to easily save some persistent variables.
"""

try:
	import cPickle as pickle
except ImportError, e:
	import pickle

from modu.persist import storable

def get(req, name, default=None):
	result = _get_variable(req, name)
	if(result is None):
		return default
	return pickle.loads(result.value)

def set(req, name, value):
	result = _get_variable(req, name)
	if(result is None):
		result = storable.Storable('variable')
		result.name = name
	result.value = pickle.dumps(value, 1)
	req.store.save(result)

def delete(req, name):
	result = _get_variable(req, name)
	if(result is not None):
		req.store.destroy(result)

def _get_variable(req, variable_name):
	req.store.ensure_factory('variable')
	result = req.store.load_one('variable', name=variable_name)
	if(result and hasattr(result.value, 'tostring')):
		result.value = result.value.tostring()
	return result
