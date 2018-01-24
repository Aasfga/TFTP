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
    def __init__(self, receiver):
        self.receiver = receiver
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.block = None

    def prepare(self, filename):
        raise NotImplementedError

    def receive_ack(self, receiver_mod):
        while not socket_empty(self.sock):
            try:
                packet, address = self.sock.recvfrom(65527)
                if address[0] != self.receiver[0]:
                    logging.debug("Data from the strange sender was received")
                op, data = parse_packet(packet)
                receiver_mod(address)
                if address != self.receiver:
                    logging.debug("Data from the wrong port was received")
                if op == 4 and data == self.block:
                    return True
                elif op == 4 and data < self.block:
                    logging.debug("Received ACK is too 'old'")
                elif op == 4 and data > self.block:
                    logging.debug("Received ACK is too 'young'")
                elif op == 5:
                    raise ConnectionError(data)
                else:
                    logging.debug("Received packet has wrong op code")
            except ValueError:
                logging.debug("The received data has an incorrect format")
        return False

    def send_data(self, packet, receiver_mod):
        time = 0.01
        for i in range(7):
            logging.debug("Waiting {} second for ACK".format(time))
            self.sock.sendto(packet, self.receiver)
            sleep(time)
            if self.receive_ack(receiver_mod):
                return
            else:
                time *= 2
        raise TimeoutError("No response from the receiver")

    def send_file(self, filename):
        file = open(filename, "r")
        end = self.prepare(filename)
        while not end:
            data = file.read(512)
            self.send_data(data_packet(self.block, data), lambda x: None)
            self.block = next_block_id(self.block)
            end = len(data) < 512

    def send_error(self, code, msg):
        self.sock.sendto(error_packet(code, msg), self.receiver)

