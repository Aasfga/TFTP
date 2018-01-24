import logging
import socket
from threading import Lock, Thread

from tftp.abstract_workers.receiver import Receiver
from tftp.abstract_workers.sender import Sender
from tftp.abstract_workers.writer import *
from tftp.packet import *


class ServerSender(Sender, Thread):
    def prepare(self, filename):
        self.block = 1
        return False

    def __init__(self, receiver, filename):
        Sender.__init__(self, receiver)
        Thread.__init__(self)
        self.filename = filename

    def run(self):
        Server.add_client(self.receiver)
        try:
            self.send_file(self.filename)
        except FileNotFoundError:
            self.send_error(1, "File not found")
        except ConnectionError as error:
            logging.error(error)
        except TimeoutError as error:
            logging.error(error)
        Server.remove_client(self.receiver)


class ServerReceiver(Receiver, Thread):
    def prepare(self, filename, writer):
        self.block = 0
        return False

    def __init__(self, sender, filename, writer_class):
        Receiver.__init__(self, sender, writer_class)
        Thread.__init__(self)
        self.filename = filename

    def run(self):
        Server.add_client(self.sender)
        try:
            self.receive_file(self.filename)
        except FileExistsError:
            self.send_error(6, "File already exists")
        except ConnectionError as error:
            logging.error(error)
        except TimeoutError as error:
            logging.error(error)
        Server.remove_client(self.sender)


class Server:
    lock = Lock()
    clients = set()
    writer = FileWriter

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
            packet, client = self.sock.recvfrom(65527)
            if self.is_in_set(client):
                continue
            try:
                op, data = parse_packet(packet)
                if op == 1:
                    logging.info("Received read request")
                    ServerSender(client, data).start()
                elif op == 2:
                    logging.info("Received write request")
                    ServerReceiver(client, data, Server.writer).start()
                else:
                    logging.info("Incorrect op code was received".format(op))
            except ValueError:
                logging.info("Incorrect packet was received")
