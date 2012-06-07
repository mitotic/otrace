#!/usr/bin/env python

from distutils.core import setup

py_modules = ["otrace"]

try:
    from collections import OrderedDict
except ImportError:
    py_modules.append("ordereddict")

setup(name='otrace',
      version='0.30',
      description='otrace: An object-oriented tracing tool for nonlinear debugging',
      author='Ramalingam Saravanan',
      author_email='sarava@sarava.net',
      url='http://info.mindmeldr.com/code/otrace',
      py_modules=py_modules,
     )
