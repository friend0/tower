__author__ = 'empire'

import wildBil
import socket
import sys

import SocketServer

class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        print "{} wrote:".format(self.client_address[0])
        print data
        socket.sendto(data.upper(), self.client_address)

class mapServer(object):

    def __init__(self, host, port):
        self.host = host;
        self.port = port;
        self.socket = openSocket(host, port)


def openSocket(host, port):
    """Open a socket on specified port with given host

    :param name: The name to use.
    :type name: str.
    :param state: Current state to be in.
    :type state: bool.
    :returns:  a socket object
    """

    HOST = host                 # Symbolic name meaning all available interfaces
    PORT = port              # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    return s


def serviceRequest(fileName):
    """This function does something.
    :param name: The name to use.
    :type name: str.
    :param state: Current state to be in.
    :type state: bool.
    :returns:  int -- the return code.
    :raises: AttributeError, KeyError
    """
    pass


class MyTCPHandler(SocketServer.BaseRequestHandler):
    """
    The RequestHandler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())

if __name__ == '__main__':
    '''
    HOST, PORT = '', 50009
    #server = SocketServer.TCPServer((HOST, PORT), MyTCPHandler)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.bind((HOST, PORT))

    print("Listening on port:", PORT)

    s.listen(1)
    conn, addr = s.accept()

    print 'Connected by', addr

    while 1:
        data = conn.recv(1024)
        print data, conn
        if not data: break
        conn.send(data)
    conn.close()
    '''
    HOST = ''                 # Symbolic name meaning all available interfaces
    PORT = 50006              # Arbitrary non-privileged port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    s.bind((HOST, PORT))
    s.listen(1)
    conn, addr = s.accept()

    print 'Connected by', addr
    while 1:
        data = conn.recv(1024)
        print data
        if not data: break
        conn.send(data)
    conn.close()


