from tftp.abstract_workers.sender import Sender
from tftp.abstract_workers.receiver import Receiver
from tftp.packet import *
import logging
from time import sleep


class ClientReceiver(Receiver):
    def change_address(self, address):
        self.target = address

    def prepare(self, filename):
        self.block = 1
        data = self.ask_for_data(rrq_packet(filename), lambda x: self.change_address(x))
        self.writer.save(data)
        return len(data) < 512


class ClientSender(Sender):
    def change_address(self, address):
        self.target = address

    def prepare(self, filename):
        self.block = 0
        self.send_data(wrq_packet(filename), lambda x: self.change_address(x))
        self.block = 1
        return False
