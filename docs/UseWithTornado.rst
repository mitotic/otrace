Using *otrace* with the Tornado web server
*********************************************************
.. sectnum::
.. contents::

This brief tutorial illustrates the use of *otrace* with the asynchronous
Tornado web server using the demo program, ``tornademos/torna_trace.py``,
included in the distribution. It is assumed that Tornado is installed
in the system (or in the ``tornademos`` directory).

Setup
=========================================================

For use with Torando, *otrace* requires a couple of additional
options, ``hold_wrapper`` and ``eventloop_callback``::

    # Initialize OShell instance (to run on separate thread)
    IO_loop = tornado.ioloop.IOLoop.instance()
    trace_shell = OShell(locals_dict=locals(), globals_dict=globals(), allow_unsafe=True,
                         init_file="torna_trace.trc", new_thread=True,
                         hold_wrapper=tornado.gen.Task,
                         eventloop_callback=IO_loop.add_callback)

    try:
        # Start oshell
        trace_shell.loop()

        # Start tornado event loop
        IO_loop.start()
    except KeyboardInterrupt:
        trace_shell.shutdown()


Holds
=========================================================

Since Tornado is a single-threaded asynchronous server, breakpoints
would halt the server. However, using the asynchronous request
handling supported by Tornado, one can *hold* the execution of a 
single request using a statement of the form::

  @tornado.web.asynchronous
  @tornado.gen.engine
  ...
  yield traceassert(number != "77", label="hold_check", action="hold")

instead of setting a breakpoint. The *hold* trace event occurs
when the trace condition is false. The ``resume`` command is used
to resume execution from a hold. Here's an example where a hold
is triggered when a user enters the number *77* in the form::

  tornademos$ ./torna_trace.py
  Listening on port 8888
    ***otrace object shell (v0.30)*** (type 'help' for info)
  globals> set trace_active True
  trace_active = True
  > rootW path=/?number=1
  rootW path=/?number=77
  GetHandler.get:hd-hold_check:21-06-24 
  > ls ~~
  /osh/recent/holds/GetHandler.get/hd-hold_check/21-06-24
  > cd ~~
  GetHandler..06-24> ls
  __down __trc  number self  
  GetHandler..06-24> ls -l
  __down = {__trc, __down, __up}
  __trc  = {thread, framestack, frame, related, funcname, context, argvalues, where, id, argstr}
  number = u'77'
  self   = <__main__.GetHandler object at 0x10ac0d950>
  GetHandler..06-24> resume
  globals>

Note that we need to activate tracing explicitly by setting parameter
``trace_active`` to True to trace ``traceassert`` calls. (This step
not needed when the ``trace`` command is used for tracing, because
tracing is automatically activated.)


/osh/web
=========================================================

The demo program ``tornademos/chat_websock.py`` is a modified version
of the chat demo program distributed with Tornado, using websockets.
If you run the program, and have one or more users chatting, you can
execute javascript commands in any user's browser via the
``/osh/web/username`` directory::

  tornademos$ ./chat_websock.py
  chat_websock: Listening on 127.0.0.1:8888
    ***otrace object shell (v0.30)*** (type 'help' for info)
  > cd /osh/web
  web> ls
  user1
  web> set safe_mode False
  safe_mode = False
  web> cd user1
  web..user1> $("body")
  [object Object]
  web..user1> $("body").css("background","red") // Change background  to red
  [object Object]

In ``chat_websock.py``, user input is handled by the input element
with id *message*.
The ``repeat`` command can be used to monitor user's typing in real time::

  web..user1> $("#message")
  [object Object]
  web..user1> repeat "User is typing: "+$("#message").val()


.. |date| date::

*Last modified:* |date|
