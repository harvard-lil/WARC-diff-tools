import uwsgi
import redis

import json
import gevent.select

class WSHandler:
    def __init__(self, env, startresponse):

        if env['PATH_INFO'] == '/':
            print('in init method')
            uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))
            r = redis.StrictRedis(host='localhost', port=6379, db=0)
            channel = r.pubsub()
            channel.subscribe('websocket')
            websocket_fd = uwsgi.connection_fd()
            redis_fd = channel.connection._sock.fileno()

            while True:
                # wait max 4 seconds to allow ping to be sent
                ready = gevent.select.select([websocket_fd, redis_fd], [], [], 4.0)
                # send ping on timeout
                if not ready[0]:
                    uwsgi.websocket_recv_nb()

                for fd in ready[0]:
                    if fd == websocket_fd:
                        # receiving
                        msg = uwsgi.websocket_recv_nb()
                        if msg:
                            # getting message from browser, publishing to redis
                             # receive, sending back answer
                            print('websocket_fd', msg)
                            r.publish('websocket', msg)
                    elif fd == redis_fd:
                        msg = channel.parse_response()
                        # self.send_to_client(msg)
                        if msg[0].decode() == 'message':
                            self.send_pong(msg[2].decode())

    def send_pong(self, msg):
        req = json.loads(msg)
        print("getting msg:", req)
        msg_to_client = {'data': 'received', 'task': 'pong'}
        self.send_to_client(msg_to_client)

    def send_to_client(self, message):
        json_response = json.dumps(message)
        uwsgi.websocket_send(json_response)
