otrace: An object-oriented tracing tool for nonlinear debugging
*********************************************************************************
.. sectnum::
.. contents::

Introduction
=============================

*otrace* is an object-oriented tracing tool for nonlinear debugging
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

*otrace* may be used as:
   - a tracing tool for debugging web servers and interactive programs
   - a console or dashboard for monitoring production servers
   - a teaching tool for exploring the innards of a program
   - a code patching tool for unit testing


Support
=============================

This README file provides a brief introduction to *otrace*. A tutorial
using a demo program is available in
`docs/GettingStarted.rst <http://info.mindmeldr.com/code/otrace/otrace-getting-started>`_
Additional documentation will be made available on the project home page,
`info.mindmeldr.com/code/otrace <http://info.mindmeldr.com/code/otrace>`_.

Report bugs and other problems using Github `Issue Tracker <https://github.com/mitotic/otrace/issues>`_.


Installation
==============================

Download the latest tagged zip archive of *otrace* from the Github
`tags page <https://github.com/mitotic/otrace/tags>`_.
The unzipped archive should contain the following files (and some more):

   ``hello_trace.py ordereddict.py otrace.py README.rst setup.py ...``

All the code for the *otrace* module is contained in a single file,
``otrace.py``. (For python 2.6 or earlier, you will also need
``ordereddict.py``.)  To use *otrace* without installing it, just
ensure that these files are  present in the module load path.
If you wish to install *otrace*, use:

   ``python setup.py install``


Usage
=================================

*otrace* does not consume any resources until some tracing action is
initiated. So it can be included in production code without any
performance penalty.
*otrace* works well with detached server processes (*daemons*)
via the GNU `screen <http://www.gnu.org/software/screen>`_
utility that emulates a terminal.
 
*otrace* is meant to be used in conjunction with an *event loop*, which
is usually present in programs that interact with users such as web
servers or GUI applications. *otrace* takes control of the terminal,
and would not work very well with programs that read user input
directly from the terminal (or standard input).

To use *otrace*, simply ``import otrace`` and instantiate the class ``otrace.OShell``,
which provides a unix-like shell interface to interact with a running
program via the terminal.

Here is a simple server example::

     import BaseHTTPServer
     from SimpleHTTPServer import SimpleHTTPRequestHandler
     from otrace import OShell, traceassert

     http_server = BaseHTTPServer.HTTPServer(("", 8888), SimpleHTTPRequestHandler)
     oshell = OShell(locals_dict=locals(), globals_dict=globals(),
                     new_thread=True, allow_unsafe=True, init_file="server.trc")
     try:
         oshell.loop()
         http_server.serve_forever()   # Main event loop
     except KeyboardInterrupt:
         oshell.shutdown()

*Usage notes:*

 - If you run in *oshell* in its own daemon thread as shown above, use
   the ^C sequence to abort the main thread, and call ``OShell.shutdown``
   from main thread to cleanup terminal I/O etc.

 - If you run *oshell* in the main thread and the event loop in a
   separate thread, ^C will abort and cleanup *oshell*. You may need to
   shutdown the event loop cleanly after that.

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
 repeat command            # Repeat command till new input is received
 resume [trace_id1..]      # Resume from breakpoint
 rm [-r] [pathname1..]     # Delete entities corresponding to pathnames (if supported)
 save [trace_id1..]        # Save current or specified trace context
 set [parameter [value]]   # Set (or display) parameter
 source filename           # Read input lines from file
 tag [(object|.) [tag_str]]    # Tag object for tracing
 trace [-a (break|debug|hold|tag)] [-c call|return|all|tag|comma_sep_arg_match_conditions] [-n +/-count] ([class.][method]|db_key|*)   # Enable tracing for class/method/key on matching condition
 unpatch class[.method]|* [> savefile]  # Unpatch method (and save patch to file)
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

