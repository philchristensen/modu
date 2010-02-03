from modu.web import app

def application(environ, start_response):
	return app.handler(environ, start_response)