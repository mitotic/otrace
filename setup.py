#!/usr/bin/env python

from setuptools import setup

py_modules = ["otrace"]

try:
    from collections import OrderedDict
except ImportError:
    py_modules.append("ordereddict")

setup(name="otrace",
      py_modules=py_modules,
      version="0.30.9",
      entry_points={"console_scripts":["otrace = otrace:main"]},
      description="otrace: An object-oriented debugger for nonlinear tracing",
      author="Ramalingam Saravanan",
      author_email="sarava@sarava.net",
      url="http://info.mindmeldr.com/code/otrace",
      download_url="https://github.com/mitotic/otrace/tags",
      license="BSD License",
      keywords=["debugging", "shell", "tracing"], 
      classifiers=[
      "Development Status :: 3 - Alpha",
      "Environment :: Console",
      "Intended Audience :: Developers",
      "License :: OSI Approved :: BSD License",
      "Operating System :: OS Independent",
      "Programming Language :: Python",
      "Programming Language :: Python :: 3",
      "Topic :: Software Development :: Debuggers",
      "Topic :: Software Development :: Libraries :: Python Modules",
      "Topic :: System :: Monitoring",
      "Topic :: System :: Shells",
      ],
      long_description="""\
otrace: An object-oriented debugger for nonlinear tracing
---------------------------------------------------------------------------

*otrace* is an object-oriented debugger for nonlinear tracing
of asynchronous or multithreaded interactive programs. It addresses
some of the limitations of sequential debugging techniques which
do not work well with server programs, where multiple requests are
handled in parallel. For example, instrumenting web servers with
print/logging statements can often result in voluminous log output
with interleaved streams of messages.

*otrace* takes a different approach to debugging that relies less on
sequential operations. Its features including taking "snapshots"
of variables for tracing, "tagging" objects for tracking across
different method invocations, and modifying live code
("monkey patching") to insert print statements etc.

*otrace* maps all the objects in the running program, as well as the
"snapshot" objects, to a virtual filesystem mounted under ``/osh``.
It provides a shell-like interface, *oshell*, with commands like
*cd*, *ls* etc. that can be used to browse classes, methods, and
instance variables in the virtual filesystem. Tab completion and
simple wildcarding are supported.
      """
     )
