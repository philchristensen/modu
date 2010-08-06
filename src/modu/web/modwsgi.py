from modu.web import app

def application(environ, start_response):
	try:
		return app.handler(environ, start_response)
	except:
		import traceback
		traceback.print_exc(None, environ['wsgi.errors'])