import logging
import socket

from tftp.abstract_workers.worker import Worker
from tftp.packet import *


def in_range(start, end, x):
    if start <= x <= end:
        return True
    if end < start and (x < end or x > start):
        return True
    return False


def calc_diff(start, x):
    if x < start:
        x += 2 ** 16
    return x - start


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
                # logging.debug(data)
                receiver_mod(address)
                if address != self.target:
                    logging.debug("Data from the wrong port was received")
                if op == 4 and in_range(self.block, self.block_end(), data):
                    return data
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

    def send_data(self, packets, receiver_mod, opt_ack):
        time = self.START_TIME
        for i in range(self.ROUNDS):
            for p in packets:
                self.sock.sendto(p, self.target)
            ack = self.receive_ack(receiver_mod, time, opt_ack)
            if ack < 0:
                time *= self.CHANGE
            else:
                return ack
        raise TimeoutError("No response from the receiver")

    def send_file(self, filename):
        file = open(filename, "rb")
        end = self.prepare(filename)
        data = []
        while not end:
            while len(data) < self.window_size:
                data.append(file.read(self.block_size))
            data = list(filter(lambda x: len(x) > 0, data))
            end = len(data[-1]) < self.block_size
            packets = []
            for i in range(self.window_size):
                packets.append(data_packet(self.block_add(i), data[i]))
            client_ack = self.send_data(packets, lambda x: None, False)
            data = data[calc_diff(self.block, client_ack) + 1:]
            self.block = client_ack
            self.block = self.block_add(1)
