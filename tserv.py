#!/usr/bin/env python
"""
Starts a Tornado static file server in a given directory.
To start the server in the current directory:
    tserv .
Then go to http://localhost:8000 to browse the directory.
Use the --prefix option to add a prefix to the served URL,
for example to match GitHub Pages' URL scheme:
    tserv . --prefix=jiffyclub
Then go to http://localhost:8000/jiffyclub/ to browse.
Use the --port option to change the port on which the server listens.
"""

from __future__ import print_function

import os
import sys
from argparse import ArgumentParser

import tornado.ioloop
import tornado.web

import base64
import uuid
from tornado.options import define, options


define("dir", default=".", type=str, help='Directory from which to serve files.')
define('port', default=8000, type=int, help='Port on which to run server.')

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class FileListHandler(BaseHandler):
    def initialize(self, path):
        self.path = path
        #return super(FileListHandler, self).initialize()

    @tornado.web.authenticated
    def get(self):
        print('current user: ', self.get_current_user())
        print('cwd: ' + self.path)
        print('uri: ' + self.request.uri)
        try:
            files = os.listdir(self.path + self.request.uri)
            self.render("index.html", pwd = self.request.uri, files = files)
        except NotADirectoryError as e:
            pass
        # self.write("hello")


class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")

def mkapp():
    settings = {
        "cookie_secret": base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
        "login_url": "/login",
        'debug': True
    }

    application = tornado.web.Application([
        (r"/", FileListHandler, dict(path=os.getcwd())),
        (r'/login', LoginHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"})
    ], **settings)

    return application


def start_server(port=8000):
    app = mkapp()
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()


def parse_args(args=None):
    parser = ArgumentParser(
        description=(
            'Start a Tornado server to serve static files out of a '
            'given directory and with a given prefix.'))
    parser.add_argument(
        '-p', '--port', type=int, default=8000,
        help='Port on which to run server.')
    parser.add_argument(
        'dir', default='.', type=str, help='Directory from which to serve files.')
    return parser.parse_args(args)


def main(args=None):
    args = parse_args(args)
    os.chdir(args.dir)
    print('Starting server on port {}'.format(args.port))
    start_server( port=args.port)


if __name__ == '__main__':
    sys.exit(main())