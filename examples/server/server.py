import os

from tftp.server import Server


print(os.getcwd())
server = Server("localhost", 6969)
server.run()

