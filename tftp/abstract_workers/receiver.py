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


class Receiver:
    def __init__(self, target, writer_class):
        self.target = target
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.block_id = None
        self.writer_class = writer_class

    def prepare(self, filename):
        raise NotImplementedError

    def file_error(self):
        raise NotImplementedError

    def receive_data(self):
        while not socket_empty(self.sock):
            try:
                packet, address = self.sock.recvfrom(4096)
                op, data = parse_packet(packet)
                if self.target is not None and self.target != address:
                    logging.warning("Strange message from strange address: {}".format(address))
                if op == 3 and data[0] == self.block_id:
                    return address, data[1]
                elif op == 3:
                    logging.warning("Wrong block id {}:{}".format(self.block_id, data[0]))
                elif op == 5:
                    raise ConnectionError(data)
                else:
                    logging.warning("strange op code {}".format(op))
            except ValueError:
                logging.warning("Received strange packet from the server")
        return None, None

    def send_ack(self):
        ack = ack_packet(self.block_id)
        time = 100
        for i in range(10):
            logging.info("Waiting {} second for data".format(time / 1000))
            self.sock.sendto(ack, self.target)
            sleep(time / 1000)
            address, data = self.receive_data()
            if data is not None:
                return data
            else:
                time *= 1.2
        raise ConnectionError("Timeout")

    def receive_file(self, filename):
        writer = self.writer_class()
        if not writer.can_create(filename):
            self.file_error()
            logging.critical("File {} exists".format(filename))
            raise FileExistsError()
        try:
            writer.open(filename)
            eof, data = self.prepare(filename)
            writer.save(data)
            while not eof:
                data = self.send_ack()
                writer.save(data)
                self.block_id = next_block_id(self.block_id)
                eof = len(data) < 512
        except Exception:
            writer.delete(filename)
            raise
        writer.close()


class ServerReceiver(Receiver):
    def prepare(self, filename):
        self.block_id = 0
        return False, ""

    def file_error(self):
        self.sock.sendto(error_packet(6, "File already exists"), self.target)
