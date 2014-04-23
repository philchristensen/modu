# modu
# Copyright (c) 2006-2010 Phil Christensen
# http://modu.bubblehouse.org
#
#
# See LICENSE for details

"""
Base package for site configuration discovery.

By implementing the ISite interface. An ISite implementor is able
to both define hostnames and paths to installed webapps, and
configure the resulting request and application objects.
"""

import os, sys

__path__ = [os.path.abspath(os.path.join(x, 'modu', 'sites')) for x in sys.path]

__all__ = []