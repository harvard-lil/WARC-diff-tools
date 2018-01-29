import os
import uwsgi
import time
import gevent.select
import redis
from werkzeug.wsgi import DispatcherMiddleware

from django.core.wsgi import get_wsgi_application
from django.conf import settings

from pywb.apps.frontendapp import FrontEndApp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


def websocket_app(env, sr):
    print("in application", env)
    print(env['PATH_INFO'])
    if env['PATH_INFO'] == '/':
        uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))
        print("websockets...!")
        r = redis.StrictRedis(host='localhost', port=6379, db=0)
        channel = r.pubsub()
        channel.subscribe('websocket')
        print("channel exists?", channel)
        websocket_fd = uwsgi.connection_fd()
        redis_fd = channel.connection._sock.fileno()

        while True:
            # wait max 4 seconds to allow ping to be sent
            ready = gevent.select.select([websocket_fd, redis_fd], [], [], 4.0)
            # send ping on timeout
            print('ready:', ready)
            if not ready[0]:
                uwsgi.websocket_recv_nb()

            for fd in ready[0]:
                print('ready[0]', ready[0])
                print('iterating on', fd, 'websocket', websocket_fd, 'redis', redis_fd)
                if fd == websocket_fd:
                    msg = uwsgi.websocket_recv_nb()
                    if msg:
                        r.publish('websocket', msg)
                elif fd == redis_fd:
                    msg = channel.parse_response()
                    print('msg, parsing response', msg)
                    # only interested in user messages
                    if msg[0].decode() == 'message':
                        uwsgi.websocket_send("[%s] %s" % (time.time(), msg))


application = DispatcherMiddleware(
    get_wsgi_application(),
    {
        '/websocket': websocket_app,
        settings.ARCHIVES_ROUTE: FrontEndApp(
            config_file='config/config.yaml',
            custom_config={'debug': True}),
    }
)
