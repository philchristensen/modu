from mod_python import Session, apache
import cPickle, time

"""
CREATE TABLE session (
  id varchar(255) NOT NULL default '',
  user_id bigint(20) unsigned NOT NULL,
  created int(11) NOT NULL default '0',
  accessed int(11) NOT NULL default '0',
  timeout int(11) NOT NULL default '0',
  data binary,
  PRIMARY KEY (id),
  KEY user_idx (user_id),
  KEY accessed_idx (accessed),
  KEY timeout_idx (timeout),
  KEY expiry_idx (accessed, timeout)
) DEFAULT CHARACTER SET utf8;
"""

class DbSession(BaseSession):
	def do_cleanup(self):
		self._req.register_cleanup(db_cleanup)
		self._req.log_error("DbSession: registered database cleanup.", apache.APLOG_NOTICE)
	
	def do_load(self):
		"SELECT s.* FROM session WHERE id = %s"
		# return {'_created':time.time(), '_accessed':time.time(), '_timeout':1800, '_data':{}}
	
	def do_save(self, dict):
		"REPLACE INTO session (id, accessed, timeout, data) VALUES (%s, %s, %s, %s)"
		# convert dict to the above format
		#self.id(), self.last_accessed(), self.timeout(), cPickle.dumps(dict)
	
	def do_delete(self):
		"DELETE FROM session s WHERE s.id = %s"
		# self.id()

def db_cleanup(data):
	"DELETE FROM session s WHERE %s - s.accessed > s.timeout"
	# int(time.time())
