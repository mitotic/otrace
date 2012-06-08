#!/usr/bin/env python

# hello_trace.py: demo application for otrace to compute reciprocal of a number

import BaseHTTPServer
import logging
import SocketServer
import sys
import urlparse

from otrace import OShell, traceassert

if sys.version_info[0] < 3:
    def encode(s):
        return s
    def decode(s):
        return s
else:
    def encode(s):
        return s.encode("utf-8")
    def decode(s):
        return s.decode("utf-8")

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

class GetHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        # Process GET request
        path_comps = urlparse.urlparse(self.path)
        query_args = urlparse.parse_qs(path_comps.query)

        logging.warning("path=%s", self.path)
        
        # Update request statistics
        Request_stats["count"] += 1
        Request_stats["path"] = self.path

        if path_comps.path == "/favicon.ico":
            self.send_error(404)
            return
        
        # Retrieve user input
        number = query_args.get("number", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        
        if number is None:
            # No user input; display input form
            resp = Page_template % ""
        else:
            # Process user input and display response
            recv = Receive(number)
            resp = Page_template % recv.respond(self)

        self.wfile.write(encode(resp))

    def log_message(self, format, *args):
        # Suppress server logging
        return

class MultiThreadedServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass

class Receive(object):
    def __init__(self, value):
        self.value = float(value)

    def respond(self, request):
        # Respond to request by computing reciprocal and returning response string

        # Diagnostic print (initially commented out)
        ##if self.value <= 0.001:
        ##    print("Client address", request.client_address)

        # Trace assertion (initially commented out)
        ##traceassert(self.value > 0.001, label="num_check")

        # Compute reciprocal of number
        response = "The reciprocal of %s is %s" % (self.value, 1.0/self.value)
        return response

if __name__ == "__main__":
    http_addr = "127.0.0.1"
    http_port = 8888

    def submit(number):
        """Simulate user form submission"""
        import urllib2
        try:
            response = urllib2.urlopen("http://%s:%s/?number=%s" % (http_addr, http_port, number))
            return "\n".join(decode(response.read()).split("\n")[-4:-3])
        except Exception, excp:
            return excp.reason if isinstance(excp, urllib2.URLError) else str(excp)

    # HTTP server
    http_server = MultiThreadedServer((http_addr, http_port), GetHandler)
    print >> sys.stderr, "Listening on %s:%s" % (http_addr, http_port)

    # Test function that raises an exception
    def test_fun():
        raise Exception("TEST EXCEPTION")

    # Initialize OShell instance (to run on separate thread)
    trace_shell = OShell(locals_dict=locals(), globals_dict=globals(), allow_unsafe=True,
                         init_file="hello_trace.trc", new_thread=True)

    try:
        # Start oshell
        trace_shell.loop()

        # Start server
        http_server.serve_forever()
    except KeyboardInterrupt:
        trace_shell.shutdown()
