import logging
import socket
from time import sleep
import select
from tftp.packet import *


def next_block_id(block):
    return (block + 1) % (2 ** 16)


def socket_empty(sock):
    ready = select.select([sock], [], [], 0)
    return ready[0] == []


class Sender:
    def __init__(self, server_address):
        self.target = server_address
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.block_id = None

    def prepare(self, filename):
        raise NotImplementedError

    def file_error(self):
        raise NotImplementedError

    def receive_ack(self):
        while not socket_empty(self.sock):
            try:
                packet, address = self.sock.recvfrom(4096)
                op, data = parse_packet(packet)
                if self.target is not None and self.target != address:
                    logger.warning("Strange message from strange address: {}".format(address))
                if op == 4 and data == self.block_id:
                    return address
                elif op == 4:
                    logger.warning("Wrong block id {}:{}".format(self.block_id, data))
                elif op == 5:
                    raise ConnectionError(data)
                else:
                    logger.warning("strange op code {}".format(op))
            except ValueError:
                logger.warning("Received strange packet from the server")
        return None

    def send_data(self, data):
        data = data_packet(self.block_id, data)
        time = 100
        for i in range(10):
            logger.info("Waiting {} second for ACK".format(time/1000))
            self.sock.sendto(data, self.target)
            sleep(time/1000)
            if self.receive_ack() is not None:
                return
            else:
                time *= 1.2
        raise ConnectionError("Timeout")

    def send_file(self, filename):
        try:
            file = open(filename, "r")
        except FileNotFoundError:
            self.file_error()
            logging.critical("File {} not found".format(filename))
            raise FileNotFoundError()
        self.prepare(filename)
        eof = False
        while not eof:
            data = file.read(512)
            eof = len(data) < 512
            self.send_data(data)
            self.block_id = next_block_id(self.block_id)


class ClientSender(Sender):
    def prepare(self, filename):
        self.block_id = 0
        server = self.target
        self.target = None
        time = 100
        for i in range(10):
            self.sock.sendto(wrq_packet(filename), server)
            logger.info("Waiting {} seconds for ACK".format(time/1000))
            sleep(time/1000)
            self.target = self.receive_ack()
            if self.target is not None:
                break
            else:
                time *= 1.2
        if self.target is None:
            raise ConnectionError("No response from the server")

    def file_error(self):
        pass


class ServerSender(Sender):
    def prepare(self, filename):
        self.block_id = 1

    def file_error(self):
        self.sock.sendto(error_packet(1, "File not found"), self.target)


logger = logging.getLogger("sender")
# logging.basicConfig(level=logging.DEBUG)
