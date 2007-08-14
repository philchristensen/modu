# modu
# Copyright (C) 2007 Phil Christensen
#
# $Id$
#
# See LICENSE for details

"""
Classes in this package define web applications installed in modu.
By implementing the ISite interface. An ISite implementor is able
to both define hostnames and paths to installed webapps, and
configure the resulting request and application objects.
"""

import os, sys

__path__ = [os.path.abspath(os.path.join(x, 'modu', 'sites')) for x in sys.path]

__all__ = []