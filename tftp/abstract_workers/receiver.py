import logging
import socket
from tftp.abstract_workers.worker import Worker
from tftp.packet import *


class Receiver(Worker):
    def __init__(self, sender, writer_class, block_size, window_size):
        super().__init__(sender, block_size, window_size)
        self.writer = None
        self.writer_class = writer_class

    def prepare(self, filename):
        raise NotImplementedError

    def receive_data(self, sender_mod, time, opt_ack):
        while time > 0:
            try:
                (packet, address), time = self.receive_packet(time)
                if address[0] != self.target[0]:
                    logging.debug("Data from the strange sender was received")
                op, data = parse_packet(packet)
                sender_mod(address)
                if address != self.target:
                    logging.debug("Data from the wrong port was received")
                if op == 3 and data[0] == self.block:
                    return data[1]
                elif op == 3 and data[0] < self.block:
                    logging.debug("Received block is too 'old'")
                elif op == 3 and data[0] > self.block:
                    logging.debug("Received block is too 'young'")
                elif op == 5:
                    raise ConnectionError(data)
                elif opt_ack and op == 6:
                    return data
                elif op == 6:
                    logging.debug("Received OACK packet")
                else:
                    logging.debug("Received packet has wrong op code")
            except ValueError:
                logging.debug("The received data has an incorrect format")
            except socket.timeout:
                logging.debug("No response for {} seconds".format(time))
                break
        return None

    def ask_for_data(self, ask_packet, sender_mod, opt_ack):
        time = self.START_TIME
        for i in range(self.ROUNDS):
            self.sock.sendto(ask_packet, self.target)
            data = self.receive_data(sender_mod, time, opt_ack)
            if data is not None:
                return data
            else:
                time *= self.CHANGE
        raise TimeoutError("No response from the sender")

    def receive_file(self, filename):
        self.writer = self.writer_class()
        if not self.writer.can_create(filename):
            raise FileExistsError
        try:
            self.writer.open(filename)
            end = self.prepare(filename)
            while not end:
                ack = ack_packet(self.block)
                self.block = self.block_add(1)
                data = self.ask_for_data(ack, lambda _: None, False)
                self.writer.save(data)
                end = len(data) < self.block_size
            self.sock.sendto(ack_packet(self.block), self.target)
        except Exception:
            self.writer.delete(filename)
            raise
        finally:
            self.writer.close()
            self.writer = None
