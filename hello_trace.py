#!/usr/bin/env python

# hello_trace.py: demo application for otrace to compute reciprocal of a number

import BaseHTTPServer
import copy
import logging
import SocketServer
import sys
import traceback
import urlparse

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
   <meta name="viewport" content="width=device-width, initial-scale=1">
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
            try:
                resp = Page_template % recv.respond(self)
            except Exception, excp:
                logging.error("ERROR: %s", excp)
                resp = "Server error:\n" + "".join(traceback.format_exception(*sys.exc_info()))

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
        ##import otrace
        ##otrace.traceassert(self.value > 0.001, label="num_check")

        # Compute reciprocal of number
        response = "The reciprocal of %s is %s" % (self.value, 1.0/self.value)
        return response

    def __deepcopy__(self, memo):
        return self.__class__(copy.deepcopy(self.value, memo))

Http_addr = "127.0.0.1"
Http_port = 8888

def submit(number, timeout=None):
    """Simulate user form submission by executing a HTTP request"""
    import urllib2
    def http_request():
        try:
            response = urllib2.urlopen("http://%s:%s/?number=%s" % (Http_addr, Http_port, number))
            resp_str = decode(response.read())
            return "\n".join(resp_str.split("\n")[-4:-3]) if resp_str.startswith("<html>") else resp_str
        except Exception, excp:
            return excp.reason if isinstance(excp, urllib2.URLError) else str(excp)
    if not timeout:
        return http_request()

    # HTTP request with timeout (run in a separate thread)
    import threading
    import Queue
    exec_queue = Queue.Queue()
    def execute_in_thread():
        exec_queue.put(http_request())
    thrd = threading.Thread(target=execute_in_thread)
    thrd.start()
    try:
        return exec_queue.get(block=True, timeout=timeout)
    except Queue.Empty:
        return "Timed out after %s seconds" % timeout

def test_fun():
    # Test function that raises an exception
    raise Exception("TEST EXCEPTION")

def run_server(args=[]):
    http_server = MultiThreadedServer((Http_addr, Http_port), GetHandler)
    print >> sys.stderr, "Listening on %s:%s (^C to stop)" % (Http_addr, Http_port)

    http_server.serve_forever()

def main(args=[]):
    # Run HTTP server
    logging.warning("hello_trace: args="+str(args))
    try:
        run_server(args)
    except KeyboardInterrupt:
        pass

def trace_main(args=[]):
    # Run HTTP server with otrace
    import otrace

    # Start otrace (in its own thread)
    oshell = otrace.set_trace(globals(), new_thread=True)

    try:
        run_server(args)
    except KeyboardInterrupt:
        # Clean shutdown of otrace (to avoid hung threads)
        oshell.shutdown()

if __name__ == "__main__":
     trace_main(args=sys.argv[1:])
