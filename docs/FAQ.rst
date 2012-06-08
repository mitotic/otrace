otrace FAQ
*********************************************************************************
.. sectnum::
.. contents::


Can all unix shell commands be used with *otrace*?
=====================================================

No. Many unix shell commands can be used when the current directory
is not ``/osh/*``. However, each unix shell command  is executed in
a separate shell process. Full-screen commands like ``vi`` will not work,
but you can use the *oshell* ``edit`` and ``view`` commands instead.
Unix shell aliases may also not work, but you can use *oshell* aliases.


Can *otrace* be used in production code? Is it secure?
======================================================

Until tracing is initiated, *otrace* simply acts like a loaded, but unused, module.
There is no performance penalty. The GNU
`screen <http://www.gnu.org/software/screen>`_ utility can be used to
provide a detachable terminal for using *otrace* with server processes. This
terminal can only be accessed by the user who owns the server process. Anyone
who is able to login with privileges to access the *otrace* terminal can directly
execute unix shell commands in any case. However, it should be kept in mind
that the power that makes *otrace* useful also makes it easier for a malicious user
to examine variables in a running program, or even modify code, without
having to edit files and restart the program. (The *safe_mode* option of *otrace*
provides limited protection from code modification.)


Does it work with Python 3?
============================================

It appears to work when ported using the ``2to3`` tool, but no real testing
has been done. 


Is there a graphical front-end to *otrace*?
============================================

There is a browser-based front-end that works, but is currently too "raw"
for public release. If you browse the code for *otrace*, you will notice the
hooks used by the front-end, which could potentially be used by other
graphical front-ends as well.
(Note: *otrace* will always remain accessible directly via the command line.)


What is *monkey patching*? Is it a good thing?
====================================================

"`Monkey patching <http://en.wikipedia.org/wiki/Monkey_patch>`_"
is a term used to refer to modification of code while a program is running.
It is generally considered a bad practice to use in production code,
although it is (or was) apparently an accepted practice in some
programming environments. It is not very commonly used in Python.
*otrace* makes it extremely easy to "monkey patch" your program,
but this feature is not meant to be used in production code. However,
it can be really useful when debugging a stateful program, because you
can keep modifying code as you learn more about the bug you are
tracking, while retaining the program state that triggers the bug. (Adding
``print`` statements to live code as you track a bug may perhaps be the
most useful feature of *otrace*.)


What is *object tagging*?
==========================================

The idea behind *object tagging* is that you can put a "marker" on an
object, by adding a special attribute, indicating that it should be traced.
Any function or method invocation where a tagged object is present in
the argument list can be automatically tracked by *otrace*. Thus, we can
follow a "rogue object" as it makes its way through the system. (It remains
to be seen how useful this feature will be in practice.)


What license is *otrace* distributed under?
============================================

The `BSD 2-clause <http://www.opensource.org/licenses/bsd-license.php>`_
open source license.
 

What platforms does *otrace* support?
============================================

*otrace* is written purely in python, but it uses OS-specific calls for some
of its operations. It has been tested on Linux and Mac OS X. With some
tweaking, its basic features should work on other plartforms.


What is ``/osh/web``?
============================================

For web servers using bi-directional
`websockets <http://en.wikipedia.org/wiki/WebSocket>`_
to communicate with the browser, hooks are provided in *otrace* to
allow the mapping of each currently connected browser to the virtual
directory ``/osh/web/username``. Once in that directory, you can type any
Javascript expression which will be sent to the browser to be evaluated
and the result will be displayed back. So the *otrace* console temporarily
acts like the Javascript console on the user's browser (e.g., like Firebug).
See the `Tornado <http://www.tornadoweb.org>`_-based
demo program ``tornademos/chat_websock.py`` for Python and
Javascript "glue code" that is needed to accomplish this.




