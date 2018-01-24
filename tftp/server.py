import logging
import socket
from threading import Lock, Thread

from tftp.abstract_workers.receiver import ServerReceiver
from tftp.abstract_workers.sender import ServerSender
from tftp.abstract_workers.writer import *
from tftp.packet import *


class Sender(Thread):
    def __init__(self, address, filename):
        super().__init__()
        self.filename = filename
        self.client = address

    def run(self):
        Server.add_client(self.client)
        try:
            ServerSender(self.client).send_file(self.filename)
        except ConnectionError as c_error:
            logger.warning(c_error)
        finally:
            Server.remove_client(self.client)


class Receiver(Thread):
    def __init__(self, address, filename):
        super().__init__()
        self.filename = filename
        self.client = address

    def run(self):
        Server.add_client(self.client)
        try:
            ServerReceiver(self.client, print_class).receive_file(self.filename)
        except ConnectionError as c_error:
            logger.warning(c_error)
        finally:
            Server.remove_client(self.client)


class Server:
    lock = Lock()
    clients = set()
    saver = PrintWriter

    @staticmethod
    def add_client(client):
        with Server.lock:
            Server.clients.add(client)

    @staticmethod
    def remove_client(client):
        with Server.lock:
            if client not in Server.clients:
                raise ValueError
            else:
                Server.clients.remove(client)

    @staticmethod
    def is_in_set(client):
        with Server.lock:
            return client in Server.clients

    def __init__(self, address, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((address, port))

    def run(self):
        while True:
            packet, client = self.sock.recvfrom(4096)
            if self.is_in_set(client):
                # logger.info("known client wants to connect")
                continue  # send error
            try:
                op, data = parse_packet(packet)
                if op == 1:
                    logger.info("Received read request")
                    Sender(client, data).start()
                elif op == 2:
                    logger.info("Received write request")
                    Receiver(client, data).start()
                else:
                    logger.warning("Wrong op code, expected 1 or 2, got {}".format(op))
            except SyntaxError:
                logger.error("can't parse packet")


print_class = PrintWriter
logger = logging.getLogger("server")
logging.basicConfig(level=logging.DEBUG)
