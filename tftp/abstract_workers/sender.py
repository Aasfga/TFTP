import logging
import socket

from tftp.abstract_workers.worker import Worker
from tftp.packet import *


class Sender(Worker):
    def prepare(self, filename):
        raise NotImplementedError

    def __init__(self, receiver, block_size, window_size):
        super().__init__(receiver, block_size, window_size)

    def receive_ack(self, receiver_mod, time, opt_ack):
        while time > 0:
            try:
                (packet, address), time = self.receive_packet(time)
                if address[0] != self.target[0]:
                    logging.debug("Data from the strange sender was received")
                op, data = parse_packet(packet)
                receiver_mod(address)
                if address != self.target:
                    logging.debug("Data from the wrong port was received")
                if op == 4 and data == self.block:
                    return True
                elif op == 4 and data < self.block:
                    logging.debug("Received ACK is too 'old'")
                elif op == 4 and data > self.block:
                    logging.debug("Received ACK is too 'young'")
                elif op == 5:
                    raise ConnectionError(data)
                elif opt_ack and op == 6:
                    return data
                elif op == 6:
                    logging.debug("OACK packet was received")
            except ValueError:
                logging.debug("The received data has an incorrect format")
            except socket.timeout:
                break
        return False

    def send_data(self, packet, receiver_mod, opt_ack):
        time = self.START_TIME
        for i in range(self.ROUNDS):
            self.sock.sendto(packet, self.target)
            if self.receive_ack(receiver_mod, time, opt_ack):
                return
            else:
                time *= self.CHANGE
        raise TimeoutError("No response from the receiver")

    def send_file(self, filename):
        file = open(filename, "rb")
        end = self.prepare(filename)
        while not end:
            data = file.read(self.block_size)
            self.send_data(data_packet(self.block, data), lambda x: None, False)
            self.block = self.block_add(1)
            end = len(data) < self.block_size
