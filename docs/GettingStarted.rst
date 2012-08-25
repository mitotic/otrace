Getting started with *otrace* and *oshell*
*********************************************************
.. sectnum::
.. contents::

This tutorial introduces the main features of *otrace* by explaining
how to "debug" the demo program, ``hello_trace.py``,
included in the distribution.

Installation
==============================

Download the development version of *otrace* from
`Github <https://github.com/mitotic/otrace/downloads>`_,
or the released archive from the
`Python Package Index <http://pypi.python.org/pypi/otrace>`_
The unzipped archive should contain the following files (and some more):

   ``hello_trace.py ordereddict.py otrace.py README.rst setup.py ...``

All the code for the *otrace* module is contained in a single file,
``otrace.py``. (For python 2.6 or earlier, you will also need
``ordereddict.py``.)  To use *otrace* without installing it, just
ensure that these files are  present in the module load path.
If you wish to install *otrace*, use:

   ``python setup.py install``


Demo program
====================================================

``hello_trace.py`` is a simple multi-threaded web server using the
``BaseHTTPServer`` module. It listens on port 8888 and displays a simple
form where the user inputs a number and the server displays the
reciprocal of the number. Inputting a zero value will raise an exception,
which will be used to illustrate the capabilities of *otrace*.

All the *oshell* commands used below are available in the script
``demo/hello_test.osh``. Once you are comfortable with the steps in
this tutorial, you can re-run the entire tutorial using the following
command (in the *otrace* console)::

  source ~~w/demo/hello_test.osh

help, cd, ls, and view commands
====================================================

Run ``hello_trace.py`` from the command line (user input appears after
the prompt ">"). The ``help`` command displays all the available *oshell* commands::

  otrace$ ./hello_trace.py
  Listening on port 8888
    ***otrace object shell (v0.30.0+)*** (type 'help' for info)
  > help
  Commands:
  alias    cd       cdls     del      dn       edit     exec     help    
  lock     ls       popd     pr       pushd    pwd      quit     repeat  
  resume   rm       run      save     set      source   swapd    tag     
  trace    unpatch  unpickle untag    untrace  up       view

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
  Page_template       Receive             Request_stats       SocketServer       
  http_addr           http_port           http_server         logging            
  send                sleep               sys                 test_fun           
  trace_shell         traceassert         urlparse           
  > ls -c
  GetHandler          MultiThreadedServer OShell              Receive            


The ``cd`` command is used to change directories. Switching to the
directory of class ``GetHandler``, we note that it supports several methods, many of which
are inherited::

  > cd GetHandler
  osh..GetHandler> ls -f
  address_string       date_time_string     do_GET               end_headers         
  finish               handle               handle_one_request   log_date_time_string
  log_error            log_message          log_request          parse_request       
  send_error           send_header          send_response        setup               
  version_string      


The ``ls`` options *-..* can be used to exclude inherited attributes
of a class, and we note that ``GetHandler`` has just one method of its own::

  osh..GetHandler> ls -f -..
  do_GET

We can examine the source code for the ``Receive.respond`` method using the
``view`` command with the *-i* (inline-display) option::

  osh..GetHandler> cd ..
  globals> cd Receive
  osh..Receive> ls
  respond
  osh..Receive> view -i respond
  def respond(self, request):
      # Respond to request by computing reciprocal and returning response string
  
      # Diagnostic print (initially commented out)
      ##if self.value <= 0.001:
      ##    print "Client address", request.client_address
  
      # Trace assertion (initially commented out)
      ##otrace.traceassert(self.value > 0.001, label="num_check")
  
      # Compute reciprocal of number
      response = "The reciprocal of %s is %s" % (self.value, 1.0/self.value)
      return response


pr and exec commands
=========================================================

The ``pr`` command prints out the value of a python expression. It is
the default command, and is assumed if no command is recognized. So
python expressions can usually be evaluated directly::

  > pwd
  /osh/globals
  > pr Request_stats
  {'count': 0, 'path': ''}
  > Request_stats["count"]
  0
  > set safe_mode False
  safe_mode = False
  > abs(Request_stats["count"] - 1)
  1

To prevent inadvertent modification of a running program through
function calls, parentheses are not allowed in ``pr`` expressions by default.
Setting the ``safe_mode`` parameter to ``False`` allows their use.

The ``exec`` command executes a python statement,
like *assignment* or *import*. The prefix *!* may be used instead
of ``exec``. ``safe_mode`` must be ``False`` to use ``exec``::

  > !Request_stats["count"] = 2


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

  globals> cd ~~g
  globals> cd Receive
  osh..Receive> trace respond
  Tracing Receive.respond
  osh..Receive> trace
  Receive.respond

Now we are ready to load the URL *http://localhost:8888* in the
browser,  and enter numbers. Instead of using the browser, in
this demo we will use the function ``submit`` that simulates browser
input from the user. The command "submit(22)" would be equivalent
to the user entering 22. A log message is generated for each value, and the
zero input value triggers a ``ZeroDivisionError`` exception in the
``respond`` method. In the exception backtrace shown below, note
the additional methods ``otrace_wrapped`` and
``otrace_function_call`` between ``do_GET`` and ``respond``.
These are inserted by ``otrace`` for tracing::

  osh..Receive> submit(3)
  rootW path=/?number=3
    <span>The reciprocal of 3.0 is 0.333333333333</span>
  osh..Receive> submit(0)
  rootW path=/?number=0
  Receive.respond:ex-ZeroDivisionError:05-08-45
  rootE ERROR: float division by zero
  Server error:
  Traceback (most recent call last):
    File "./hello_trace.py", line 76, in do_GET
      resp = Page_template % recv.respond(self)
    File "/Users/rsarava/app4/repo/mitotic/otrace/otrace.py", line 4601, in otrace_wrapped
      return cls.otrace_function_call(func_info, *args, **kwargs)
    File "/Users/rsarava/app4/repo/mitotic/otrace/otrace.py", line 4373, in otrace_function_call
      return_value = info.fn(*args, **kwargs)
    File "./hello_trace.py", line 104, in respond
      response = "The reciprocal of %s is %s" % (self.value, 1.0/self.value)
  ZeroDivisionError: float division by zero

When a trace condition occurs, like an exception in a traced function or method, a trace id
``GetHandler.respond:ex-ZeroDivisionError:05-08-45`` is generated and displayed,
as shown above. Also, the default action of the ``trace`` command is
to create a new virtual directory
``/osh/recent/exceptions/GetHandler.respond/ex-ZeroDivisionError/05-08-45``
to hold the *trace context* for the event. The shorthand notation
**~~** can be used  to display the most recent *trace context*::

  osh..Receive> ls ~~
  /osh/recent/exceptions/Receive.respond/ex-ZeroDivisionError/05-08-45
  osh..Receive> cd ~~

The trace context contains information about the function like
argument values and the call stack.::

  Receive..08-45> ls
  __trc   __up    request self   
  Receive..08-45> ls -l
  __trc   = {exc_context, thread, framestack, frame, related, funcname, context, exc_stack, where, id, argvalues}
  __up   = {path_comps, __trc, __up, __down, number, self, recv, query_args}
  request = <__main__.GetHandler instance at 0x106760fc8>
  self    = <__main__.Receive object at 0x1068cb090>
  Receive..08-45> cd __trc
  osh..__trc> ls
  argvalues   context     exc_context exc_stack   frame       framestack  funcname   
  id          related     thread      where      
  osh..__trc> ls -l where
  where =
  '__bootstrap-->__bootstrap_inner-->run-->process_request_thread-->finish_request-->__init__-->handle-->handle_one_request-->do_GET-->respond'


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
call to ``traceassert``. (Actually ``hello_trace.py`` already has a
``traceassert`` call that is commented out. We simply uncomment it,
as well as the diagnostic ``print`` statement, via the ``edit`` command.)::

  osh..__trc> cd ~~g
  globals> set safe_mode False
  safe_mode = False
  globals> set trace_active True
  trace_active = True
  globals> edit Receive.respond
  Patched Receive.respond:

Note that we need to activate tracing explicitly by setting parameter
``trace_active`` to True to trace ``traceassert`` calls. (This step
not needed when the ``trace`` command is used, because tracing is
automatically activated.)
After the edit, the statement ``otrace.traceassert(number > 0.001, label="num_check")``
has been inserted into ``Receive.respond``. In the browser, enter the number
2 and then the number 0.0005. The latter value triggers a false
condition on the ``traceassert``. We switch to the assert trace
context directory ``/osh/recent/asserts/Receive.respond/as-num_check/04-57-54``,
which allows us to examine the local variables when the assertion failed::

  globals> submit(2)
  rootW path=/?number=2
    <span>The reciprocal of 2.0 is 0.5</span>
  globals> submit(0.0005)
  rootW path=/?number=0.0005
  Client address ('127.0.0.1', 62008)
  Receive.respond:as-num_check:05-08-51 
    <span>The reciprocal of 0.0005 is 2000.0</span>
  globals> ls ~~
  /osh/recent/asserts/Receive.respond/as-num_check/05-08-51
  globals> cd ~~
  Receive..08-51> ls
  __up  __trc   request self   
  Receive..08-51> self.value
  0.0005
  Receive..08-51> request.headers
  Accept-Encoding: identity
  Host: 127.0.0.1:8888
  Connection: close
  User-Agent: Python-urllib/2.7

The default action when the traceassert condition is false is to
create the trace context directory. The ``action`` argument to
``traceassert`` can be used set a breakpoint when the assertion fails.
For efficiency, the trace context for ``traceassert`` does not save the
backtrace stack local variables or source code information by default.
To enable backtracing of stack and source code, ``set assert_context``
to a non-zero value.


unpatch and untrace
=========================================================

After debugging is complete, the ``unpatch`` command can be used to
restore  the original code for ``Receive.respond``. 
The ``untrace`` command can be used to switch off tracing::

  globals> cd /osh/patches
  patches> ls
  Receive.respond
  patches> unpatch Receive.respond
  Unpatching Receive.respond
  patches> cd ~~g
  patches> trace
  Receive.respond
  globals> untrace Receive.respond
  untraced Receive.respond
  globals>


Object tag tracing
=========================================================

One of the allowed actions in the ``trace -a <action> -c <condition> ...``
command is ``tag``. The tag action adds a special attribute to the
``self`` object if the trace condition is met at the time a function
returns. The tag attribute is just a string, usually the object's
``id``, but can also be the current time or some other string.
The presence of tagged arguments can be specified as a trace condition
for subsequent tracing of a function, using the ``-c tagged[<argname>]``
option. The commands ``tag`` and ``untag`` can be used to directly
add/remove the tag attribute.

In the example below, the method ``Receive.__init__`` will tag the
``self`` object if ``self.value`` equals 1 when the method returns.
Then, we trace ``Receive.respond`` if its argument named ``self``
is tagged. First, we submit the value 2, which does not trigger
tagging. Next, we submit the value 1, which causes the ``self``
object to be tagged when ``Receive.__init__`` returns, and
then triggers a trace context for ``Receive.respond`` because
one of its arguments is tagged::

  globals> cd ~~g
  globals> trace -a tag -c self.value==1 Receive.__init__
  Tracing -a tag -c {'self.value==': 1L} Receive.__init__
  globals> trace -c taggedself Receive.respond
  Tracing -c taggedself Receive.respond
  globals> submit(2)
  rootW path=/?number=2
    <span>The reciprocal of 2.0 is 0.5</span>
  globals> submit(1)
  rootW path=/?number=1
  Receive:tg-self.value==1;0x103231090:17-04-42 
  Receive.respond:tr-taggedself;tg-self.value==1;0x103231090:17-04-42.0 self=<__main__.Receive object at 0x103231090>, request=<__main__.GetHandler instance at 0x10322f950>
    <span>The reciprocal of 1.0 is 1.0</span>
  globals> cd ~~
  Receive..04-42.0> pwd
  /osh/recent/traces/Receive.respond/tr-taggedself;tg-self.value==1;0x103231090/17-04-42.0
  Receive..04-42.0> ls
  __trc   request self   


Preserving trace contexts
=========================================================

Only a limited number of trace contexts (controlled by ``set max_recent``)
are retained in memory. If there are too many contexts, the oldest
contexts are deleted. The  ``save`` command can be used to preserve
trace contexts in memory. The ``set pickle_file`` command can be used
to specify a *pickle* database file in which to save all trace
contexts. This pickle database file can be opened at a later time
using the ``unpickle`` command to read trace contexts into the
``/osh/pickled`` directory::

  Receive..04-42.0> cd ~~g
  globals> set pickle_file trace_test.db
  pickle_file = trace_test.db
  globals> trace Receive.respond
  Tracing Receive.respond
  globals> submit(0)
  ...
  globals> unpickle trace_test.db
  globals> cd /osh/pickled
  pickled> ls
  exceptions
  pickled> cd
  exceptions/Receive.respond/ex-ZeroDivisionError/17-06-22.0/:
  osh..:> ls
  __trc   __up    request self   
  osh..:> 

The special directory ``:`` is used to denote the content of the trace
context.


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
Other possible actions for ``trace`` and ``traceassert`` include
``pdb`` or ``ipdb``, which launch the respective debuggers at the
breakpoint. The ``continue`` command of the debuggers should be used
to return control to *otrace*.

.. |date| date::

*Last modified:* |date|
