import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import os.path

from tornado.options import define, options

import easywebdav

define('port', default=8000, help='run on the given port', type=int)

class Application(tornado.web.Application):
    def __init__(self):

        handlers = [
            (r"/", MainHandler),
            (r"/ls", MainHandler)
        ]
        settings = dict(
            cookie_secret="__SOMETHING_GOES_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


def recurse_path(dav, path):
    ls = dav.ls(path)

    dir = []
    for f in ls:
        newest = {}

        if f[0] in path:
            continue

        p = str(f[0]).replace('/remote.php/webdav/', '')
        if len(p) > 0:
            logging.info( "found object: %r", f)

            newest['path'] = str(f[0]).replace('/remote.php/webdav/', '')
            newest['size'] = f[1]
            newest['mtime'] = f[2]
            newest['ctime'] = f[3]
            newest['content-type'] = f[4]
            newest['subdir'] = None

            if p.endswith('/'):
                logging.info("determined directory, traversing...")

                newest['subdir'] = recurse_path(dav, '/remote.php/webdav/'+p)

                dir.append(newest)
                dir.extend(newest['subdir'])
            else:
                dir.append(newest)

    return dir

class MainHandler(tornado.web.RequestHandler):
    def get(self):

        self.render('index.html')

    def post(self):

        username = self.get_argument('username')
        password = self.get_argument('word')
        host     = self.get_argument('host')
        uri      = self.get_argument('uri')

        webdav = easywebdav.connect(host, username=username, password=password, protocol='https', port=443, verify_ssl=True)

        dir = recurse_path(webdav, uri)

        self.render('listing.html', files=dir)

        logging.info( "Directory: %r", dir)

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
