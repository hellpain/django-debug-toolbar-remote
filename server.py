#coding: utf-8
import time
import thread
import pickle
import logging
import zmq
import Queue
import tornado.ioloop
import tornado.web
from sockjs.tornado import SockJSConnection, SockJSRouter


class IndexHandler(tornado.web.RequestHandler):
    """Regular HTTP handler to serve the ping page"""
    def get(self):
        self.render('index.html')


class BroadcastConnection(SockJSConnection):
    clients = set()

    def on_open(self, info):
        self.clients.add(self)

    def on_message(self, msg):
        if message_queue.empty():
            self.broadcast(self.clients, None)
        else:
            new_debug_report = message_queue.get()
            self.broadcast(self.clients, new_debug_report)

    def on_close(self):
        self.clients.remove(self)


BroadcastRouter = SockJSRouter(BroadcastConnection, '/broadcast')

main_loop = None


def tornado_thread():

    logging.getLogger().setLevel(logging.DEBUG)

    static_path = '/home/hellpain/dev/remote-django-debug-toolbar/static/'
    app = tornado.web.Application(
        [(r"/", IndexHandler), ] + BroadcastRouter.urls + [(r'(.*)', tornado.web.StaticFileHandler, {'path': static_path}),]
    )
    app.listen(8080)

    print('Listening on 0.0.0.0:8080')
    main_loop = tornado.ioloop.IOLoop.instance()
    main_loop.start()


socket = None


def zeromq_thread():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind('tcp://127.0.0.1:43000')
    while True:
        try:
            data = pickle.loads(socket.recv())
            print data
            message_queue.put(data)
            socket.send('ok')
        except Exception as e:
            print(e)

message_queue = None

if __name__ == '__main__':
    message_queue = Queue.Queue()
    thread.start_new_thread(tornado_thread, ())
    thread.start_new_thread(zeromq_thread, ())

    while True:
       time.sleep(1)