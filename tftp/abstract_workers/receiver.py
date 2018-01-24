import logging
import socket
from time import sleep
import select
from tftp.packet import *


def next_block(block):
    return (block + 1) % (2 ** 16)


def socket_empty(sock):
    ready = select.select([sock], [], [], 0)
    return ready[0] == []


class Receiver:
    def __init__(self, sender, writer_class):
        self.sender = sender
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.block = None
        self.writer_class = writer_class

    def prepare(self, filename, writer):
        raise NotImplementedError

    def receive_data(self, sender_mod):
        while not socket_empty(self.sock):
            try:
                packet, address = self.sock.recvfrom(65527)
                if address[0] != self.sender[0]:
                    logging.debug("Data from the strange sender was received")
                op, data = parse_packet(packet)
                sender_mod(address)
                if address != self.sender:
                    logging.debug("Data from the wrong port was received")
                if op == 3 and data[0] == self.block:
                    return data[1]
                elif op == 3 and data[0] < self.block:
                    logging.debug("Received block is too 'old'")
                elif op == 3 and data[0] > self.block:
                    logging.debug("Received block is too 'young'")
                elif op == 5:
                    raise ConnectionError(data)
                else:
                    logging.debug("Received packet has wrong op code")
            except ValueError:
                logging.debug("The received data has an incorrect format")
        return None

    def ask_for_data(self, ask_packet, sender_mod):
        time = 0.01
        for i in range(7):
            logging.debug("Waiting {} seconds for data".format(time))
            self.sock.sendto(ask_packet, self.sender)
            sleep(time)
            data = self.receive_data(sender_mod)
            if data is not None:
                return data
            else:
                time *= 2
        raise TimeoutError("No response from the sender")

    def receive_file(self, filename):
        writer = self.writer_class()
        if not writer.can_create(filename):
            raise FileExistsError
        try:
            writer.open(filename)
            end = self.prepare(filename, writer)
            while not end:
                ack = ack_packet(self.block)
                self.block = next_block(self.block)
                data = self.ask_for_data(ack, lambda _: None)
                writer.save(data)
                end = len(data) < 512
            self.sock.sendto(ack_packet(self.block), self.sender)
        except Exception:
            writer.delete(filename)
            raise
        finally:
            writer.close()

    def send_error(self, code, msg):
        self.sock.sendto(error_packet(code, msg), self.sender)