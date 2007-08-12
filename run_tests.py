#!/usr/bin/env python

import os, os.path

directory = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.join(directory, 'test')
os.system("find %s -maxdepth 1 -name 'test_*.py' -exec trial --temp-directory=/tmp/_trial \{\} \;" % test_dir)

