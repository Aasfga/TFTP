import os

from tftp.server import Server

server = Server("localhost", 6969)
server.run()

