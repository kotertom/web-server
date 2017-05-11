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

from tornado.httpclient import HTTPClient, AsyncHTTPClient, HTTPError
from tornado.options import define, options


define("dir", default=".", type=str, help='Directory from which to serve files.')
define('port', default=8000, type=int, help='Port on which to run server.')

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class FileListHandler(BaseHandler):
    def initialize(self, path):
        self.cwd = path
        #return super(FileListHandler, self).initialize()

    @tornado.web.authenticated
    def get(self, path):
        print('current user: ', self.get_current_user())
        print('cwd: ' + self.cwd)
        print('path: ' + path)
        print('uri: ' + self.request.uri)
        print('new path: ' + os.path.join(self.cwd, path))
        try:
            #is it a dir?
            # os.chdir(path)
            # self.cwd = os.curdir
            files = os.listdir(os.path.join(self.cwd, path))
            parentdir = os.path.pardir if path else ""
            print('parentdir: ' + parentdir)
            self.render("index.html", pwd = self.request.uri, files = files, lpwd = path, parentdir = parentdir)
        except NotADirectoryError as e:
            #it's a file
            self.sendFile(path)


    def sendFile(self, path):
        filepath = os.path.join(self.cwd, path)
        filename = os.path.split(self.request.uri)[-1]
        if not self.request.uri or not os.path.exists(filepath):
            raise HTTPError(404)
        self.set_header('Content-Type', 'application/force-download')
        self.set_header('Content-Disposition', 'attachment; filename=%s' % filename)
        with open(filepath, "rb") as f:
            try:
                while True:
                    _buffer = f.read(4096)
                    if _buffer:
                        self.write(_buffer)
                    else:
                        f.close()
                        self.finish()
                        return
            except:
                raise HTTPError(404)
        raise HTTPError(500)

class LoginHandler(BaseHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>')

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name"))
        self.redirect("/")


class UploadHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self, path):
        cwd = os.getcwd()
        print('upload path: ' + path)
        # print('file: ' + self.request.files['filearg'][0])
        for field_name, files in self.request.files.items():
            print('field_name: ' + field_name)
            for info in files:
                filename, content_type = info['filename'], info['content_type']
                body = info['body']
                print('filepath: ' + os.path.join(path, filename))
                with open(os.path.join(path, filename), 'wb') as out:
                    out.write(bytes(body))
                    print('file written!')
        self.redirect('/' + path)


def mkapp():
    settings = {
        "cookie_secret": base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes),
        "login_url": "/login",
        'debug': True
    }

    application = tornado.web.Application([
        (r'/login', LoginHandler),
        (r"/static/(.*)", tornado.web.StaticFileHandler, {"path": "static"}),
        (r"/upload/(.*)", UploadHandler),
        (r"/(.*)", FileListHandler, dict(path=os.getcwd()))
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