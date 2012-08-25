otrace: An object-oriented python debugger for nonlinear tracing
*********************************************************************************
.. sectnum::
.. contents::

**NOTE**: This README file describes the development version of
*otrace* on `GitHub <https://github.com/mitotic/otrace/downloads>`_.
For a description of the `released version <http://pypi.python.org/pypi/otrace>`_,
see the README file included with the distribution, or the
`project website <http://info.mindmeldr.com/code/otrace>`_.

Introduction
=============================

*otrace* is an object-oriented debugger for nonlinear tracing
of asynchronous or multithreaded interactive python programs.
It addresses some of the limitations of sequential debugging
techniques which do not work well with server programs, where
multiple requests are handled in parallel. For example,
instrumenting web servers with print/logging statements can often
result in voluminous log output with interleaved streams of messages.

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

*otrace* may be used as:
   - a tracing tool for debugging web servers and interactive programs
   - a console or dashboard for monitoring production servers
   - a teaching tool for exploring the innards of a program
   - a code patching tool for unit testing

*otrace* is best suited for use with "long-running" programs like
GUI applications or servers that interact with users. Typically,
these programs have an *event loop* that runs until the program
is shutdown. *otrace* runs in its own thread, and enables debugging
of the running program.

*otrace* takes control of the terminal, and would not work very
well with programs that read user input directly from the terminal
(or standard input). However, *otrace* has a browser-based graphical
front-end, `GraphTerm <http://info.mindmeldr.com/code/graphterm>`_,
that can be used with programs that do read from the terminal.

*otrace* does not consume any resources until some tracing action is
initiated. So it can be included in production code without any
performance penalty. It also works well with detached server
processes (*daemons*) via the GNU
`screen <http://www.gnu.org/software/screen>`_ terminal emulator,
or using the GraphTerm front-tend.


Installation
==============================

If you wish to install *otrace* without the sample programs, the ``easy_install otrace``
command should be sufficient (provided the ``setuptools`` module is installed).

The latest released version of *otrace*, including sample programs,
may be downloaded from the `Python Package Index <http://pypi.python.org/pypi/otrace>`_
The untarred/unzipped archive should contain the following files (and some more):

   ``hello_trace.py ordereddict.py otrace.py README.rst setup.py ...``

All the code for the *otrace* module is contained in a single file,
``otrace.py``. (For python 2.6 or earlier, you will also need
``ordereddict.py``.)  To use *otrace* without installing it, just
ensure that these files are  present in the module load path.
If you wish to install *otrace*, use:

   ``python setup.py install``

The development version of *otrace* may be downloaded from
`Github <https://github.com/mitotic/otrace/downloads>`_.


Support
=============================

 - This README file provides a brief introduction to *otrace*.

 - Report bugs and other issues using the Github `Issue Tracker <https://github.com/mitotic/otrace/issues>`_.

 - A tutorial using a demo program is available in
    `docs/GettingStarted.rst <http://info.mindmeldr.com/code/otrace/otrace-getting-started>`_.

 - `Python and the Holy Grail of Debugging <https://dl.dropbox.com/u/72208800/code/Python-debugging-APUG-jun13.pdf>`_:  slides from a talk given at the Austin Python Users Group.

 - Additional documentation and updates will be made available on the *project home page*,
   `info.mindmeldr.com/code/otrace <http://info.mindmeldr.com/code/otrace>`_.


Using otrace from the command line
=============================================================================

If you have a program ``example.py`` whose execution you wish to
trace, use the ``otrace`` command (or the program ``otrace.py``, if
you have not installed *otrace*)::

  otrace example.py

You will see the *otrace* console. To execute a function ``main()`` in
``example.py``, type the following command::

  run main

To execute the function ``test(arg=[])`` that accepts a single
argument that is a list of strings, type::

  run test arg1 arg2

You can also invoke this function directly from the command line as
follows::

  otrace -f test example.py arg1 arg2

In this case, the program will exit when the function ``test``
returns.
(At this time, only functions that accept no arguments, or a single
optional argument that is a list of strings, can be invoked directly
from the command line or using the ``run`` command.)


Using otrace from within a program
=============================================================================

Although command line use of *otrace* may be sufficient for simple
cases, you may wish to include *otrace* within your program for more
complex situations. In a program with an event loop, *otrace* would be
typically included as follows::

  import otrace
  # Start otrace (in its own thread)
  oshell = otrace.set_trace(globals(), new_thread=True)
  try:
      # Run main program event loop ...
  except KeyboardInterrupt:
      # Clean shutdown of otrace (to avoid hung threads)
      oshell.shutdown()

Similar to *pdb*, *otrace* can also be invoked "as needed" within a program as follows::

  import otrace
  otrace.set_trace(globals())

In this case, *otrace* will run in the calling thread, and the calling program
will resume only after the ``quit`` command is typed in the *otrace*
console.

For interactively running functions in a program, you would include
*otrace* as follows::

  import otrace
  otrace.set_trace(globals(), wait_to_run=true)

In this case, *otrace* will run in a separate thread, but will wait
for the ``run`` command to invoke a function in the main thread.
(A new ``run`` command can be issued only after the function returns.)


*Usage notes:*

 - If you run in *oshell* in its own daemon thread as shown above, use
   the Control-C sequence to abort the main thread, and call ``shutdown``
   from the main thread to cleanup.

 - Install the python ``readline`` module (``easy_install readline``) to enable *TAB* command completion.

 - To start a detached server (daemon) process, use the command:
      ``screen -d -m -S <screen_name> <executable> <argument1> ...``
   To attach a terminal to this process, use:
      ``screen -r <screen_name>``

 - By default, *otrace* logs to the ``logging`` module. Subclass
   ``TraceCallback``, overriding the methods ``callback`` and ``returnback``
   to implement your own logging  (see ``DefaultCallback`` for a simple example)

Implementation
==========================================

*otrace* uses a *Virtual Directory Shell Interface* which maps all the
objects in a a running python program to a virtual filesystem mounted in
the directory ``/osh`` (sort of like the unix ``/proc`` filesystem, if you are
familiar with it). Each module, class, method, function, and variable in the global namespace
is mapped to a virtual file within this directory.
For example, a class ``TestClass`` in the ``globals()`` dictionary can be accessed as::

   /osh/globals/TestClass

and a method ``test_method`` can be accessed as::

   /osh/globals/TestClass/test_method

and so on.

*otrace* provides a unix shell-like interface, *oshell*, with commands
such as ``cd``, ``ls``, ``view``, and ``edit`` that can be used navigate, view,
and edit the virtual files. Editing a function or method
"`monkey patches <http://en.wikipedia.org/wiki/Monkey_patch>`_"  it,
allowing the insertion of ``print`` statements etc. in the running program.

The ``trace`` command allows dynamic tracing of function or method invocations,
return values, and exceptions. This is accomplished by
dynamically *decorating* (or *wrapping*) the function to be traced.
When a trace condition is satisfied, the function-wrapper saves
*context information*, such as arguments and return values,
in a newly created virtual directory in::

    /osh/recent/*

These *trace context* directories can be navigated just like
``/osh/globals/*``. (If there are too many trace contexts, the oldest
ones are deleted, unless they have been explicitly *saved*.)

*oshell* allows standard unix shell commands to be interspersed with
*oshell*-specific commands. The path of the "current working directory"
determines which of the these two types of commands will be executed. 
If the current working directory is not in ``/osh/*``, the command is
treated as a standard unix shell command (except for ``cd``, which is
always handled by *oshell*.)


Commands
=================
*oshell* supports the following commands ([..] denotes optional
parameters; | denotes alternatives)::


 alias name cmd <arg\*> <arg\1>... # Define alias for command
 cd [pathname]             # change directory to "pathname", which may be omitted, "..", or "/" or a path
 cdls [pathname]           # cd to "pathname" and list "files" (cd+ls)
 del [trace_id1..]         # Delete trace context
 dn                        # Command alias to move one level down in stack frames in a trace context (to a newer frame)
 edit [-f] (filename|class[.method]) [< readfile]  # Edit/patch file/method/function
 exec python_code          # Execute python code (also !<python_code>)
 help [command|*]          # Display help information
 lock                      # Lock terminal until password is entered
 ls [-acflmtv] [-(.|..|.baseclass)] [pathname1|*]   # List pathname values (or all pathnames in current "directory")
 pr python_expression      # Print value of expression (DEFAULT COMMAND)
 pwd                       # Print current working "directory"
 quit                      # Quit shell
 run function [arg1 ...]   # Run function in main thread with optional string list argument
 repeat command            # Repeat command till new input is received
 resume [trace_id1..]      # Resume from breakpoint
 rm [-r] [pathname1..]     # Delete entities corresponding to pathnames (if supported)
 save [trace_id1..]        # Save current or specified trace context
 set [parameter [value]]   # Set (or display) parameter
 source filename           # Read input lines from file
 tag [(object|.) [tag_str]]    # Tag object for tracing
 trace [-a (break|ipdb|pdb|hold|tag)] [-c call|return|all|tag|comma_sep_arg_match_conditions] [-n +/-count] ([class.][method]|db_key|*)   # Enable tracing for class/method/key on matching condition
 unpatch class[.method]|* [> savefile]  # Unpatch method (and save patch to file)
 unpickle filename [field=value]        # Read pickled trace contexts from file 
 untag [object|.]          # untag object
 untrace ([class.][method]|*|all)  # Disable tracing for class/method
 up                        # Command alias to move one level up in stack frames in a trace context (to an older frame)
 view [-d] [-i] [class/method/file]  # Display source/doc for objects/traces/files

The default command is ``pr``, which evaluates an expression.  So you
can simply type a python variable to print out its value. You can also
insert ``otrace.traceassert(<condition>,label=..,action=..)`` to trace
assertions.


Python 3
===============================

``otrace.py`` and the demo program ``hello_trace.py`` work with Python
3, after porting using the ``2to3`` tool. Further testing remains to be done.


Caveats
===============================

 - *Reliability:*  This software has not been subject to extensive testing. Use at your own risk.

 - *Thread safety:* In principle, *otrace* should thread-safe, but more testing is needed to confirm this in practice.

 - *Memory leaks:*  The trace contexts saved by *otrace* could potentially lead to increased memory usage. Again, only experience will tell.

 - *Platforms:*  *otrace* is pure-python, but with some OS-specific calls for file, shell, and terminal-related operations. It has been tested only on Linux and Mac OS X so far, although the demo program works with the Windows console as well.

 - *Current limitations:*
          * Decorated methods cannot be patched.
          * TAB command completion is a work in progress.
          * Spaces and other special characters in command arguments need to be handled better.

Credits
===============================

*otrace* was developed as part of the `Mindmeldr <http://mindmeldr.com>`_ project, which is aimed at improving classroom interaction.

*otrace* was inspired by the following:
 - the tracing module `echo.py <http://wordaligned.org/articles/echo>`_ written by Thomas Guest <tag@wordaligned.org>. This nifty little program uses decorators to trace function calls.

 - the python ``dir()`` function, which treats objects as directories. If objects are directories, then shouldn't we be able to inspect them using the familiar ``cd`` and ``ls`` unix shell commands?

 - the unix `proc <http://en.wikipedia.org/wiki/Procfs>`_ filesystem, which cleverly maps non-file data to a filesystem interface mounted at ``/proc``

 - the movie `Being John Malkovich <http://en.wikipedia.org/wiki/Being_John_Malkovich>`_ (think of ``/osh`` as the portal to the "mind" of a running program)


License
=====================

*otrace* is distributed as open source under the `BSD-license <http://www.opensource.org/licenses/bsd-license.php>`_.

