Getting started with *otrace* and *oshell*
*********************************************************
.. sectnum::
.. contents::

This tutorial introduces the main features of *otrace* by explaining
how to "debug" the demo program, ``hello_trace.py``,
included in the distribution.

Installation
==============================

Download the latest version of the *otrace* 
`zip archive <https://github.com/mitotic/otrace/zipball/master>`_.
The unzipped archive should contain the following files (and perhaps more):

   ``hello_trace.py ordereddict.py otrace.py README.rst setup.py``

All the code for the *otrace* module is contained in a single file,
``otrace.py``. To use it without installing it, just ensure that it is 
present in the module load path. If you wish to install *otrace*, type:

  ``python setup.py install``

(On python 2.5, you will also need to install ``ordereddict.py``.)

help, cd, ls, and view commands
====================================================

``hello_trace.py`` is a simple multi-threaded web server using the
``BaseHTTPServer`` module. It listens on port 8888 and displays a simple
form where the user inputs a number and the server displays the
reciprocal of the number. Inputting a zero value will raise an exception,
which will be used to illustrate the capabilities of *otrace*.

Run ``hello_trace.py`` from the command line (user input appears after
the prompt ">"). The ``help`` command displays all the available *oshell* commands::

  otrace$ ./hello_trace.py
  Listening on port 8888
    ***otrace object shell (v0.30)*** (type 'help' for info)
  > help
  Commands:
  alias   cd      cdls    del     dn      edit    exec    help    ls      popd   
  pr      pushd   pwd     quit    read    repeat  resume  rm      save    set    
  swapd   tag     trace   tracing unpatch untag   untrace up      view   

  If you omit the command, "pr" is assumed.
  Use TAB key for command completion.
  Type "help <command>" or "help *" for more info

  See http://info.mindmeldr.com/code/otrace for documentation
  globals> help pwd
  pwd [-a]                  # Print current working "directory"

  -a Print all paths in stack; top first

The ``pwd`` command displays the current working directory.
The ``ls`` command displays directory names and content. The special directory name **~~**
refers to the most recent *trace context*, and is initially
``/osh/globals``.  There are also other special directory names of the
form ~~<letter>::

  > pwd
  /osh/globals
  > ls ~~
  /osh/globals
  > ls ~~g
  /osh/globals
  > ls ~~w
  /Users/rsarava/app4/repo/meldr-hg/otrace

The ``ls`` options *-c*, *-f*, *-m*, *-v* can be used to selectively display
only the *classes*, *functions/methods*, *modules*, and *variables* in
a directory. Initially we examine the ``globals`` directory, which
contains three classes, ``GetHandler, MultiThreadedServer, and OShell``::

  > ls
  BaseHTTPServer      GetHandler          MultiThreadedServer OShell             
  Page_template       Request_stats       SocketServer        http_addr          
  http_port           http_server         logging             sys                
  test_fun            trace_shell         traceassert         urlparse           
  > ls -c
  GetHandler          MultiThreadedServer OShell             

The ``cd`` command is used to change directories. Switching to the
directory of class ``GetHandler``, we note that it supports several methods, many of which
are inherited::

  > cd GetHandler
  osh..GetHandler> pwd
  /osh/globals/GetHandler
  osh..GetHandler> ls -f
  address_string       date_time_string     do_GET              
  end_headers          finish               handle              
  handle_one_request   log_date_time_string log_error           
  log_message          log_request          parse_request       
  respond              send_error           send_header         
  send_response        setup                version_string      

The ``ls`` options *-..* can be used to exclude inherited attributes
of a class, and we note that ``GetHandler`` has two methods of its own::

  osh..GetHandler> ls -f -..
  do_GET  respond

We can examine the source code for the ``respond`` method using the
``view`` command with the *-i* (inline-display) option::

 osh..GetHandler> view -i respond
 def respond(self, number):
     # Respond to request by processing user input
     number = float(number)

     # Diagnostic print (initially commented out)
     ##if number <= 0.001:
     ##    print "Client address", self.client_address

     # Trace assertion (initially commented out)
     ##traceassert(number > 0.001, label="num_check")

     # Compute reciprocal of number
     response = "The reciprocal of %s is %s" % (number, 1.0/number)
     return response

trace command
===============================================

The ``trace`` command is used to trace functions and methods. Without
any options, it simply traces exceptions.  The ``-c <condition>``
option, where ``<condition>`` may be 
``call``, ``return``, or ``all``, may be used to trace function/method
calls, returns, or both. ``<condition>``  may also be
``argname1.comp1==value1,argname2!=value2,...`` to trace on argument
value matching (values with commas/spaces must be quoted; the special
argument name ``return`` may also be used).
Without any arguments, the ``trace`` command displays currently traced names.
Next, we initiate tracing on the ``respond`` method  using the
``trace`` command::

  osh..GetHandler> trace respond
  Tracing GetHandler.respond
  osh..GetHandler> trace
  GetHandler.respond

Now we load the URL *http://localhost:8888* in the browser, and enter
the number 3 followed by the number zero in the input form. A log message
is generated for each value, and the zero value triggers a
``ZeroDivisionError`` exception in the ``respond`` method.
In the exception backtrace shown below, note the additional methods ``wrapped``
and ``trace_function_call`` between ``do_GET`` and ``respond``. These
are inserted by ``otrace`` for tracing::

  rootW path=/?number=3
  rootW path=/?number=0
  GetHandler.respond:ex-ZeroDivisionError:23-01-33
  ----------------------------------------
  Exception happened during processing of request from ('127.0.0.1', 59872)
  Traceback (most recent call last):
    ...
    File "./hello_trace.py", line 61, in do_GET
      self.wfile.write(Page_template % self.respond(number))
    File "/Users/rsarava/app4/repo/meldr-hg/otrace/otrace.py", line 4535, in wrapped
      return cls.trace_function_call(info, *args, **kwargs)
    File "/Users/rsarava/app4/repo/meldr-hg/otrace/otrace.py", line 4289, in trace_function_call
      return_value = info.fn(*args, **kwargs)
    File "./hello_trace.py", line 71, in respond
      response = "The reciprocal of %s is %s" % (number, 1.0/number)
  ZeroDivisionError: float division by zero
  ----------------------------------------
 
When a trace condition occurs, like an exception in a traced function or method, a trace id
``GetHandler.respond:ex-ZeroDivisionError:23-01-33`` is generated and displayed,
as shown above. Also, the default action of the ``trace`` command is
to create a new virtual directory
``/osh/recent/exceptions/GetHandler.respond/ex-ZeroDivisionError/23-01-33``
to hold the *trace context* for the event. The shorthand notation
**~~** can be used  to display the most recent *trace context*::

  > ls ~~
  /osh/recent/exceptions/GetHandler.respond/ex-ZeroDivisionError/23-01-33
  > cd ~~
  GetHandler..01-33> pwd
  /osh/recent/exceptions/GetHandler.respond/ex-ZeroDivisionError/23-01-33

The trace context contains information about the function like
argument values and the call stack.::

  GetHandler..01-33> ls
  __down __trc  number self  
  GetHandler..01-33> ls -l
  __down = {path_comps, __trc, __up, __down, number, self, query_args}
  __trc  = {exc_context, thread, framestack, frame, related, funcname, context, exc_stack, where, id, argvalues}
  number = 0.0
  self   = <__main__.GetHandler instance at 0x108a34d88>
  GetHandler..01-33> cd __trc
  osh..__trc> ls
  argvalues   context     exc_context exc_stack   frame       framestack 
  funcname    id          related     thread      where      
  osh..__trc> ls -l where
  where =  '__bootstrap-->__bootstrap_inner-->run-->process_request_thread-->
  finish_request-->__init__-->handle-->handle_one_request-->do_GET-->respond'
  osh..__trc> 
  

edit and traceassert
=========================================================

The ``edit`` command is perhaps the most useful command in *otrace*. It
allows you to modify (`monkey patch <http://en.wikipedia.org/wiki/Monkey_patch>`_) any function or method in the
running program. In particular, it makes it easy to use the "oldest"
debugging technique, viz., inserting ``print`` statements in the code,
without having to modify the actual source code files.

Now that we know the there is an exception occurring in the method
``respond``, we pretend that we don't know the exact cause, and will
use the ``traceassert`` function to determine the cause. The ``traceassert``
functions has the signature ``traceassert(condition, label="", action="")``.
As long as ``condition`` is true, ``traceassert`` simply returns. If
``condition`` is false, the call is logged and a *trace context*
virtual directory is created. 

We suspect that the exception is caused because the user entered a
number that was too small. First, we switch off *safe mode*, which
disallows code editing. We then use the ``edit`` command to modify
the ``respond`` method in the running program to insert a
call to ``traceasset``. (Actually ``hello_trace.py`` already has a
``traceassert`` call that is commented out. We simply uncomment it,
as well as the diagnostic ``print`` statement, via the ``edit`` command.)::

  osh..__trc> cd ~~g
  globals> set safe_mode false
  safe_mode = False
  globals> edit GetHandler.respond
  Patched GetHandler.respond:

Now the call ``traceassert(number > 0.001, label="num_check")`` has been
inserted into ``GetHandler.respond``. In the browser, enter the number
2 and then the number 0.0005. The latter value triggers a false
condition on the ``traceassert``. We switch to the assert trace
context directory ``/osh/recent/asserts/GetHandler.respond/as-num_check/23-40-13``,
which allows us to examine the local variables when the assertion failed::

  rootW path=/?number=2
  rootW path=/?number=0.0005
  Client address ('127.0.0.1', 64211)
  GetHandler.respond:as-num_check:23-40-13 

  > ls ~~
  /osh/recent/asserts/GetHandler.respond/as-num_check/23-40-13
  > cd ~~
  GetHandler..40-13> ls
  __down __trc  number self  
  GetHandler..40-13> self.headers["User-Agent"]
  Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.5 Safari/534.55.3
  GetHandler..40-13> self.client_address
  ('127.0.0.1', 64211)

The default action when the traceassert condition is false is to
create the trace context directory. The ``action`` argument to
``traceassert`` can be used set a breakpoint when the assertion fails.

unpatch and untrace
=========================================================

After debugging is complete, the ``unpatch`` command can be used to
restore  the original code for ``GetHandler.respond``. 
The ``untrace`` command can be used to switch off tracing::

  globals> cd /osh/patches
  patches> ls
  GetHandler.respond
  patches> unpatch GetHandler.respond
  Unpatching GetHandler.respond
  patches> cd ~~g
  patches> trace
  GetHandler.respond
  globals> untrace GetHandler.respond
  untraced GetHandler.respond
  globals> 

Monitoring using the repeat command
=========================================================

The ``repeat`` command indefinitely repeats whatever command that
follows it, erasing the screen each time before displaying the
output. The default repeat interval is 0.2 seconds, and that
can be changed via the ``set repeat_interval`` command.
Any user input, or a trace event will end the repeat cycle.
Here's an example of using ``repeat`` to monitor the requests
processed by the demo the web server::

> repeat ls -l Request_stats/*


Breakpoints
=========================================================

Breakpoints can be set using the ``-a break`` option for the ``trace``
command, or the ``action="break"`` argument to ``traceassert``.
The ``resume`` command is used to resume execution from a breakpoint.


.. |date| date::

*Last modified:* |date|
