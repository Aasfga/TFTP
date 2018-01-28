from tftp.abstract_workers.sender import Sender
from tftp.abstract_workers.receiver import Receiver
from tftp.packet import *
import logging
from time import sleep


class ClientReceiver(Receiver):
    def change_address(self, address):
        self.target = address

    def set_options(self, options):
        try:
            self.block_size = int(options["blocksize"])
            self.window_size = int(options["windowsize"])
        except KeyError:
            self.send_error(8, "Incorrect options")
            raise

    def prepare(self, filename):
        self.block = 0
        options = self.ask_for_data(
            rrq_packet(filename, {"blocksize": self.block_size, "windowsize": self.window_size}),
            lambda x: self.change_address(x), True, {})
        self.set_options(options[-5])
        return False


class ClientSender(Sender):
    def change_address(self, address):
        self.target = address

    def set_options(self, options):
        try:
            self.block_size = int(options["blocksize"])
            self.window_size = int(options["windowsize"])
        except KeyError:
            self.send_error(8, "Incorrect options")
            raise

    def prepare(self, filename):
        self.block = 1
        options = self.send_data(wrq_packet(filename, {"blocksize": self.block_size, "windowsize": self.window_size}),
                                 lambda x: self.change_address(x),
                                 True)
        self.set_options(options)
        return False
