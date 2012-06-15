#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# Modified for testing otrace.py using websockets
# - Replaced Google auth with dummy login auth
#

import cgi
import Cookie
import functools
import logging
import os.path
import uuid

import tornado.auth
import tornado.gen
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.wsgi

import otrace

try:
    import json
except ImportError:
    import simplejson as json

from tornado.options import define, options
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

class Application(tornado.web.Application):
    def __init__(self):
        message_handler = tornado.wsgi.WSGIContainer(WSGIApp.create)

        handlers = [
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/chatsocket", ChatSocketHandler),
            (r".*", tornado.web.FallbackHandler, dict(fallback=message_handler)),
        ]
        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
        )


        tornado.web.Application.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json: return None
        return tornado.escape.json_decode(user_json)


class WSGIApp(object):
    app_name = "chat_websock"
    users = {}
    websockets = OrderedDict()
    cache = []
    cache_size = 200
    states = OrderedDict()
    max_states = 1000
    loader = None
    static_prefix = "/static"
    template_dir = "templates"

    @classmethod
    def static_url(cls, path):
        return cls.static_prefix + "/" + path

    @classmethod
    def localize(cls, text):
        return text

    @classmethod
    def linkify(cls, text, **kwargs):
        return tornado.escape.linkify(text, **kwargs)

    @classmethod
    def drop_state(cls, state_id):
        try:
            del cls.states[state_id]
        except Exception:
            pass

    @classmethod
    def add_state(cls, state):
        if len(cls.states) >= cls.max_states:
            cls.states.pop(last=False)
        state_id = str(uuid.uuid4())
        cls.states[state_id] = state
        return state_id

    @classmethod
    def add_websocket(cls, username, websocket):
        if username in cls.websockets:
            try:
                cls.websockets[username].close()
            except Exception:
                pass
        cls.websockets[username] = websocket
        cls.users[username] = {}

    @classmethod
    def drop_websocket(cls, username):
        try:
            del cls.users[username]
        except Exception:
            pass
        try:
            del cls.websockets[username]
        except Exception:
            pass

    @classmethod
    def create(cls, environ, start_response):
        wsgi_app = cls()
        return wsgi_app.run(environ, start_response)

    @classmethod
    def render_string(cls, template_name, **kwargs):
        if not cls.loader:
            cls.loader = tornado.template.Loader(cls.template_dir, autoescape=None)
        args = {"app_name": cls.app_name, "static_url": cls.static_url, "_": cls.localize,
                "linkify": cls.linkify, "Template": cls.render_string}
        args.update(kwargs)
        return cls.loader.load(template_name).generate(**args)

    @classmethod
    def make_message(cls, body, name):
        message = {
            "id": str(uuid.uuid4()),
            "from": name,
            "body": body,
        }
        message["html"] = cls.render_string("message.html", message=message)
        return message

    def __init__(self):
        pass

    def redirect(self, url):
        headers = [ ("Location", url) ]
        status_str = "302 Found"
        self.start_response(status_str, headers)
        return [""]

    def html_response(self, body):
        headers = [('Content-Type', 'text/html')]
        self.start_response('200 OK', headers)
        return [ body ]

    def json_response(self, obj):
        headers = [('Content-Type', 'text/json')]
        self.start_response('200 OK', headers)
        return [ json.dumps(obj) ]

    def run(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

        self.path = environ["PATH_INFO"]

        if not self.path.startswith("/"):
            raise tornado.web.HTTPError(400, "Bad Request")
        
        path_comps = self.path[1:].split("/")
        action = path_comps[2] if len(path_comps) > 2 else ""

        client_cookie = Cookie.SimpleCookie(environ.get("HTTP_COOKIE", ""))
        if self.app_name not in client_cookie:
            return self.redirect("/auth/login")
            
        state_id = client_cookie[self.app_name].value
        if not state_id or state_id not in self.states:
            return self.redirect("/auth/login")

        self.state = self.states[state_id]

        # Parse form data
        self.form_data = cgi.FieldStorage(fp=environ["wsgi.input"], environ=environ, keep_blank_values=True)

        if not action:
            return self.html_response(self.render_string("index_ws.html",
                      messages=WSGIApp.cache, username=self.state["username"], path=self.path))
        elif action == "new":
            return self.new()
        else:
            raise tornado.web.HTTPError(400, "Bad Request: "+action)

    def new(self):
        message = self.make_message(self.form_data.getfirst("body", ""), self.state["username"])
        if message["body"] == "raise":
            raise Exception("raise message")

        otrace.OTrace.traceassert(message["body"] != "assert", label="assert_id1")

        self.update_cache([message])

        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(self.broadcast, [message]))

        if self.form_data.getfirst("next", ""):
            return self.redirect(self.form_data.getfirst("next"))
        else:
            return self.json_response(message)

    @classmethod
    def broadcast(cls, messages):
        logging.info("Sending new message to %r listeners", len(cls.websockets))
        body_str = json.dumps({"messages": messages})
        headers = [('Content-Type', 'text/json')]
        status_str = '200 OK'

        for websocket in cls.websockets.values():
            try:
                websocket.write_message(body_str)
            except Exception, excp:
                logging.warning("ERROR in writing to websocket: %s; closing", excp)
                try:
                    websocket.close()
                except Exception:
                    pass

    @classmethod
    def update_cache(cls, messages):
        cls.cache.extend(messages)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    def updates(self):
        # Get message cursor from URL query string
        cursor = self.form_data.getfirst("cursor", None)

        if cursor:
            index = 0
            for i in xrange(len(self.cache)):
                index = len(self.cache) - i - 1
                if self.cache[index]["id"] == cursor: break
            recent = self.cache[index + 1:]
            if recent:
                # Have messages to display; return right away
                logging.info("Displaying %d available messages", len(recent))
                headers = [('Content-Type', 'text/json')]
                self.start_response('200 OK', headers)
                body_str = json.dumps({"messages": recent})
                return [ body_str ]


class ChatSocketHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        self.state = None
        super(ChatSocketHandler, self).__init__(application, request, **kwargs)

    def allow_draft76(self):
        # for iOS 5.0 Safari
        return True

    def open(self):
        pass

    def on_close(self):
        WSGIApp.drop_websocket(self.state["username"])

    def on_message(self, message):
        logging.info("got message %r", message)
        if not self.state:
            if message not in WSGIApp.states:
                logging.warning("Invalid state %r; closing websocket", message)
                self.close()
                return
            self.state = WSGIApp.states[message]
            WSGIApp.add_websocket(self.state["username"], self)
            return
        parsed_data = tornado.escape.json_decode(message)

        if "stdout" in parsed_data:
            TraceInterface.receive_output(self.state["username"], parsed_data)
            return

        chat_msg = WSGIApp.make_message(parsed_data["body"], self.state["username"])

        WSGIApp.update_cache([chat_msg])
        WSGIApp.broadcast([chat_msg])

class AuthLoginHandler(BaseHandler):
    def get(self):
        self.write("""<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body><form action="/auth/login" method="post">
Name: <input type="text" name="username">
<input type="submit" value="Sign in">
</form></body>
</html>""")

    def post(self):
        user = {"username": self.get_argument("username")}
        state_id = WSGIApp.add_state(user)
        self.set_secure_cookie("user", tornado.escape.json_encode(user))
        self.set_cookie(WSGIApp.app_name, state_id)
        self.redirect("/")

class AuthLogoutHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        state_id = self.get_cookie(WSGIApp.app_name)
        if state_id:
            WSGIApp.drop_state(state_id)
        self.clear_cookie("user")
        self.clear_cookie(WSGIApp.app_name)
        if user:
            self.write("<h1>User %s has been signed out.</h1>" % user["username"])
        else:
            self.redirect("/")

# OTrace websocket interface
class TraceInterface(object):
    root_depth = 1   # Max. path components for web directory (below /osh/web)
    trace_hook = None

    @classmethod
    def set_web_hook(cls, hook):
        cls.trace_hook = hook

    @classmethod
    def get_root_tree(cls):
        """Returns directory dict tree (with depth=root_depth) that is updated automatically"""
        return WSGIApp.users

    @classmethod
    def send_command(cls, path_comps, command):
        """ Send command to browser via websocket (invoked in the otrace thread)
        path_comps: path component array (first element identifies websocket)
        command: Javascript expression to be executed on the browser
        """
        # Must be thread-safe
        websocket = WSGIApp.websockets.get(path_comps[0])
        if not websocket:
            cls.trace_output([], "", "No such socket: %s" % path_comps[0])
            return

        # Schedules callback in event loop
        tornado.ioloop.IOLoop.instance().add_callback(functools.partial(websocket.write_message,
                                                                        json.dumps({"stdin": command})))

    @classmethod
    def receive_output(cls, username, message):
        """Receive stdout/stderr output from browser via websocket and forward to oshell
        message = {'stdout':..., 'stderr': ...}
        """
        cls.trace_output([username], message["stdout"], message.get("stderr"))

    @classmethod
    def trace_output(cls, path_comps, stdout, stderr=None):
        """ Send stdout/stderr output to oshell (invoked in the eventloop)
        path_comps: path component array (first element identifies websocket)
        """
        # Writing output to otrace stdout/stderr should be thread-safe
        if stderr:
            cls.trace_hook("stderr", path_comps, stderr)
        cls.trace_hook("stdout", path_comps, stdout)
        

def main():
    define("console", default=logging.WARNING, help="console_logging_level", type=int)
    define("port", default=8888, help="run on the given port", type=int)
    define("addr", default="127.0.0.1", help="IP address")

    tornado.options.parse_command_line()

    logging.getLogger().setLevel(options.console)

    app = Application()
    app.listen(options.port, address=options.addr)
    print "chat_websock: Listening on %s:%s" % (options.addr, options.port)

    IO_loop = tornado.ioloop.IOLoop.instance()
    trace_shell = otrace.OShell(locals_dict=locals(), globals_dict=globals(), allow_unsafe=True,
                                web_interface=TraceInterface,
                                init_file="chat_websock.trc", new_thread=True,
                                hold_wrapper=tornado.gen.Task,
                                eventloop_callback=IO_loop.add_callback)

    try:
        trace_shell.loop()
        IO_loop.start()
    except KeyboardInterrupt:
        trace_shell.shutdown()


if __name__ == "__main__":

    main()
