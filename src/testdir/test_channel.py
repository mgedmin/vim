#!/usr/bin/python
#
# Server that will accept connections from a Vim channel.
# Run this server and then in Vim you can open the channel:
#  :let handle = ch_open('localhost:8765', 'json')
#
# Then Vim can send requests to the server:
#  :let response = ch_sendexpr(handle, 'hello!')
#
# And you can control Vim by typing a JSON message here, e.g.:
#   ["ex","echo 'hi there'"]
#
# There is no prompt, just type a line and press Enter.
# To exit cleanly type "quit<Enter>".
#
# See ":help channel-demo" in Vim.
#
# This requires Python 2.6 or later.

from __future__ import print_function
import json
import socket
import sys
import threading

try:
    # Python 3
    import socketserver
except ImportError:
    # Python 2
    import SocketServer as socketserver

thesocket = None

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        print("=== socket opened ===")
        global thesocket
        thesocket = self.request
        while True:
            try:
                data = self.request.recv(4096).decode('utf-8')
            except socket.error:
                print("=== socket error ===")
                break
            except IOError:
                print("=== socket closed ===")
                break
            if data == '':
                print("=== socket closed ===")
                break
            print("received: {}".format(data))
            try:
                decoded = json.loads(data)
            except ValueError:
                print("json decoding failed")
                decoded = [-1, '']

            # Send a response if the sequence number is positive.
            # Negative numbers are used for "eval" responses.
            if decoded[0] >= 0:
                if decoded[1] == 'hello!':
                    # simply send back a string
                    response = "got it"
                elif decoded[1] == 'make change':
                    # Send two ex commands at the same time, before replying to
                    # the request.
                    cmd = '["ex","call append(\\"$\\",\\"added1\\")"]'
                    cmd += '["ex","call append(\\"$\\",\\"added2\\")"]'
                    print("sending: {}".format(cmd))
                    thesocket.sendall(cmd.encode('utf-8'))
                    response = "ok"
                elif decoded[1] == '!quit!':
                    # we're done
                    sys.exit(0)
                else:
                    response = "what?"

                encoded = json.dumps([decoded[0], response])
                print("sending: {}".format(encoded))
                thesocket.sendall(encoded.encode('utf-8'))

        thesocket = None

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    HOST, PORT = "localhost", 0

    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)

    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

    # Write the port number in Xportnr, so that the test knows it.
    f = open("Xportnr", "w")
    f.write("{}".format(port))
    f.close()

    # Block here
    print("Listening on port {}".format(port))
    server.serve_forever()
