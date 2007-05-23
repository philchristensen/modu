# dathomir
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

def handler(request):
    try:
        from mod_python import apache
        
        request.content_type = "text/plain"
        request.write("Hello World! Again.")
        return apache.OK
    except ImportError, e:
        pass