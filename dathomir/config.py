from dathomir.util import urlnode
from dathomir import session, persist
from mod_python import apache

_site_tree = urlnode.URLNode()

db_url = 'mysql://dathomir:dathomir@localhost/dathomir'
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
	
	rsrc = _site_tree.parse(req.dathomir_path)
	if not(rsrc):
		return apache.HTTP_NOT_FOUND
	
	req.approot = apache.get_handler_root()
	
	req.db = init_database()
	req.session = init_session(req, req.db)
	req.user = req.session.get_user()
	req.store = init_store(req.db)
	
	rsrc.prepare_content(req)
	req.content_type = rsrc.get_content_type(req)
	content = rsrc.get_content(req)
	req.set_content_length(len(content))
	req.write(content)
	
	return apache.OK

def init_database():
	import urlparse
	global db_url
	
	dsn = urlparse.urlparse(db_url)
	if(dsn.scheme == 'mysql'):
		connection = MySQLdb.connect(dsn.netloc, dsn.username, dsn.password, dsn.path)
	else:
		raise NotImplementedError("Unsupported database driver: '%s'" % dsn.scheme)
	
	return connection

def init_store(connection):
	store = persist.Store(connection)
	return store

def init_session(req, connection):
	sess = session.UserSession(req, connection)
	return sess