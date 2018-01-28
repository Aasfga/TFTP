import logging
import socket
from threading import Lock, Thread

from tftp.abstract_workers.receiver import Receiver
from tftp.abstract_workers.sender import Sender
from tftp.abstract_workers.writer import *
from tftp.packet import *


class ServerSender(Sender, Thread):
    def prepare(self, filename):
        self.block = 0
        self.send_data([opt_packet({"blocksize": self.block_size, "windowsize": self.window_size})],
                       lambda _: None, False)
        self.block = self.block_add(1)
        return False

    def __init__(self, receiver, filename, block_size, window_size):
        Sender.__init__(self, receiver, block_size, window_size)
        Thread.__init__(self)
        self.filename = filename

    def run(self):
        Server.add_client(self.target)
        try:
            self.send_file(self.filename)
        except FileNotFoundError:
            self.send_error(1, "File not found")
        except ConnectionError as error:
            logging.error(error)
        except TimeoutError as error:
            logging.error(error)
        Server.remove_client(self.target)


class ServerReceiver(Receiver, Thread):
    def prepare(self, filename):
        self.block = 1
        data = self.ask_for_data(opt_packet({"blocksize": self.block_size, "windowsize": self.window_size}),
                          lambda _: None,
                          False)
        self.writer.save(data)
        return data < self.block_size

    def __init__(self, sender, filename, writer_class, block_size, window_size):
        Receiver.__init__(self, sender, writer_class, block_size, window_size)
        Thread.__init__(self)
        self.filename = filename

    def run(self):
        Server.add_client(self.target)
        try:
            self.receive_file(self.filename)
        except FileExistsError:
            self.send_error(6, "File already exists")
        except ConnectionError as error:
            logging.error(error)
        except TimeoutError as error:
            logging.error(error)
        Server.remove_client(self.target)


class Server:
    lock = Lock()
    clients = set()
    writer = FileWriter

    @staticmethod
    def add_client(client):
        with Server.lock:
            Server.clients.add(client)
        logging.info("Client {} was added".format(client))

    @staticmethod
    def remove_client(client):
        with Server.lock:
            if client not in Server.clients:
                raise ValueError
            else:
                Server.clients.remove(client)
        logging.info("Client {} was removed".format(client))

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
                op, (filename, options) = parse_packet(packet)
                bs, ws = int(options["blocksize"]), int(options["windowsize"])
                if op == 1:
                    logging.info("Received read request. Block_size: {}, window_size: {}".format(bs, ws))
                    ServerSender(client, filename, bs, ws).start()
                elif op == 2:
                    logging.info("Received write request. Block_size: {}, window_size: {}".format(bs, ws))
                    ServerReceiver(client, filename, Server.writer, bs, ws).start()
            except ValueError:
                logging.info("Incorrect packet was received")
            except TypeError:
                logging.info("Incorrect op code was received")
            except KeyError:
                logging.info("Incorrect options")
