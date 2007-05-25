from dathomir.util import urlnode
from mod_python import apache

_site_tree = urlnode.URLNode()

base_path = '/'

def activate(rsrc):
	global _site_tree
	for path in rsrc.get_paths():
		_site_tree.register(path, rsrc)

def handler(req):
	global base_path
	if(req.uri.startswith(base_path)):
		req.dathomir_path = req.uri[len(base_path):]
	else:
		req.dathomir_path = req.uri
	
	req.approot = apache.get_handler_root()
	
	rsrc = _site_tree.parse(req.dathomir_path)
	if not(rsrc):
		return apache.HTTP_NOT_FOUND
	
	rsrc.prepare_content(req)
	req.content_type = rsrc.get_content_type(req)
	content = rsrc.get_content(req)
	req.set_content_length(len(content))
	req.write(content)
	
	return apache.OK