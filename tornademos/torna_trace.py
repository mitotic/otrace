#!/usr/bin/env python

# torna_trace.py: demo application using the tornado web server to compute reciprocal of a number
#  - used to illustrate capabilities of otrace.py

import logging
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from tornado.options import define, options

from otrace import OShell, traceassert

Page_template = """<html>
<head>
   <title>Hello Trace</title>
</head>
<body>
  <h2>Hello Trace</h2>
  <form method="get" action="/">
    Find reciprocal of:
    <input id="number" name="number" type="text" autocomplete="off" autofocus="autofocus"></input>
    <input type="submit" value="Submit" />
  </form>
  <p>
  <span>%s</span>
</body>
</html>
"""

# Request statistics
Request_stats = {"count":0, "path":""}

class GetHandler(tornado.web.RequestHandler):
    def get(self):
        logging.warning("path=%s", self.request.uri)

        # Update request statistics
        Request_stats["count"] += 1
        Request_stats["path"] = self.request.uri

        # Retrieve user input
        number = self.get_argument("number", None)

        if number is None:
            # No user input; display input form
            self.write(Page_template % "")
        else:
            # Process user input and display response
            self.write(Page_template % self.respond(number))

    def respond(self, number):
        # Respond to request by processing user input
        number = float(number)

        # Trace assertion (initially commented out)
        ##traceassert(number > 0.001, label="num_check")

        # Compute reciprocal of number
        response = "The reciprocal of %s is %s" % (number, 1.0/number)
        return response
        

if __name__ == "__main__":
    # Define command line options
    define("port", default=8888, help="run on the given port", type=int)

    tornado.options.options.logging = "none"    # Disable tornado logging
    tornado.options.parse_command_line()

    # Set up tornado application to handle "/" url only
    app = tornado.web.Application(handlers=[(r'/', GetHandler)])

    # Start tornado HTTP server
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    print >> sys.stderr, "Listening on port %d" % options.port

    # Test function that raises an exception
    def test_fun():
        raise Exception("TEST EXCEPTION")

    # Initialize OShell instance (to run on separate thread)
    trace_shell = OShell(locals_dict=locals(), globals_dict=globals(), allow_unsafe=True,
                         init_file="torna_trace.trc", new_thread=True)

    try:
        # Start oshell
        trace_shell.loop()

        # Start tornado event loop
        IO_loop = tornado.ioloop.IOLoop.instance()
        IO_loop.start()
    except KeyboardInterrupt:
        trace_shell.shutdown()
