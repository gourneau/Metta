#!/usr/bin/env python
"""
Connect to it with:
  telnet localhost 6000
"""
import gevent
from gevent.server import StreamServer
from gevent.queue import Queue
import logging

logging.basicConfig(level=logging.DEBUG)

class ConnectionHandler(object):
    
    def __init__(self):
        self.connection_index = 0
        self.clients = {}
        self.all_messages = []
    
    def get_connection_id(self):
        self.connection_index += 1
        return self.connection_index
    
    def on_new_client(self, socket, address):
        print 'New client from %s:%s' % address
        client_id = self.get_connection_id()
        
        in_queue, out_queue = Queue(), Queue()
        self.clients[client_id] = {
            'in': in_queue,
            'out': out_queue,
            'socket': socket,
            'subscribers': set()
        }

        out_queue.put_nowait('{%s}' % client_id)
 
        gevent.joinall([
            gevent.spawn(self.handle_incoming, client_id),
            gevent.spawn(self.handle_outgoing, client_id),
        ])
    __call__ = on_new_client

    def on_new_message(self, client_id, message):
        client = self.clients[client_id]
        # place in clients in queue
        client['in'].put(message)
        
        # store in global list
        #JOSH: I don't care about things persisting
        self.all_messages.append((client_id, message))
        logging.debug('got message: %s', (client_id, message))
        
        # notify any subscribers
        for subscriber in client['subscribers']:
            self.clients[subscriber]['out'].put('[%s] %s' % (client_id, message))

        # stupid "parsing"
        handler = 'default'
        if ':' in message:
            parts = message.split(':', 1)
            handler, message = parts

        getattr(self, '_handle_%s' % handler, self._handle_default)(client_id, message)
    
    def _handle_default(self, client_id, message):
        logging.info('message being handled by "default" handler')
        """
        for id,client in self.clients.items():
            if id == client_id:
                continue
            client['out'].put_nowait('new message from %s: %s' % (client_id, message))
        """

    def _handle_subscribe(self, source_id, other_id):
        logging.info('message being handled by "subscribe" handler')
        other_id = int(other_id.strip())
        source = self.clients[source_id]
        
        #TODO: check to see if they exist yet
        
        if other_id not in self.clients:
            out.put('"%s" is not a valid id' % other_id)
        else:
            other = self.clients[other_id]
            other['subscribers'].add(source_id)
            source['out'].put('subscribed to "%s"' % other_id)
            other['out'].put('"%s" subscribed to you' % source_id)


    def handle_incoming(self, client_id):
        client = self.clients[client_id]
        f = client['socket'].makefile()
        while True:
            line = f.readline()
            if not line:
                print "client %s disconnected" % client_id
                break
            if line.strip().lower() == 'quit':
                print "client quit"
                break
            gevent.spawn(self.on_new_message, client_id, line)
            
    def handle_outgoing(self, client_id):
        client = self.clients[client_id]
        f = client['socket'].makefile()
        while True:
            f.write(client['out'].get()+'\n')
            f.flush()

        # @todo handle cleanup

if __name__ == '__main__':
    server = StreamServer(('0.0.0.0', 6000), ConnectionHandler())
    print 'Starting server on port 6000'
    server.serve_forever()
