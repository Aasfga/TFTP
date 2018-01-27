import logging

from tftp.server import Server

logging.basicConfig(level=logging.DEBUG)
server = Server("localhost", 6969)
server.run()

