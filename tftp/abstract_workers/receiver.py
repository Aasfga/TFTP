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


class Receiver(Worker):
    def __init__(self, sender, writer_class, block_size, window_size):
        super().__init__(sender, block_size, window_size)
        self.writer = None
        self.writer_class = writer_class

    def prepare(self, filename):
        raise NotImplementedError

    def receive_data(self, sender_mod, time, opt_ack, window):

        while time > 0:
            try:
                (packet, address), time = self.receive_packet(time)
                if address[0] != self.target[0]:
                    logging.debug("Data from the strange sender was received")
                op, data = parse_packet(packet)
                # logging.debug(data)
                sender_mod(address)
                if address != self.target:
                    logging.debug("Data from the wrong port was received")
                if op == 3 and in_range(self.block, self.block_end(), data[0]):
                    # logging.debug("Received data {}".format(data[0]))
                    window[data[0]] = data[1]
                    if len(window) == self.window_size:
                        return window
                elif op == 3 and data[0] < self.block:
                    logging.debug("Received block is too 'old'")
                elif op == 3 and data[0] > self.block:
                    logging.debug("Received block is too 'young'")
                elif op == 5:
                    raise ConnectionError(data)
                elif opt_ack and op == 6:
                    return {-5: data}
                elif op == 6:
                    logging.debug("Received OACK packet")
                else:
                    logging.debug("Received packet has wrong op code")
            except ValueError:
                logging.debug("The received data has an incorrect format")
            except socket.timeout:
                logging.debug("No response for {} seconds".format(time))
                break
        return window

    def correct(self, window):
        crr = self.block
        for i in window:
            if abs(i - crr) > 1:
                return False
        return True

    def ask_for_data(self, ask_packet, sender_mod, opt_ack, window):
        time = self.START_TIME
        for i in range(self.ROUNDS):
            self.sock.sendto(ask_packet, self.target)
            window = self.receive_data(sender_mod, time, opt_ack, window)
            if not self.correct(window):
                return window
            elif len(window) == self.window_size:
                return window
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
            window = {}
            while not end:
                ack = ack_packet(self.block)
                self.block = self.block_add(1)
                window = self.ask_for_data(ack, lambda _: None, False, window)
                end = True
                for i in range(self.block, self.block + self.window_size):
                    i %= 2 ** 16
                    self.block = i
                    if i in window:
                        end = len(window[i]) < self.block_size
                        self.writer.save(window[i])
                        del window[i]
                    else:
                        break

            self.sock.sendto(ack_packet(self.block), self.target)
        except Exception:
            self.writer.delete(filename)
            raise
        finally:
            self.writer.close()
            self.writer = None
