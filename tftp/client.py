from tftp.abstract_workers.sender import Sender
from tftp.abstract_workers.receiver import Receiver
from tftp.packet import *
import logging
from time import sleep


class ClientReceiver(Receiver):
    def prepare(self, filename):
        self.block_id = 1
        server = self.target
        self.target = None
        time = 100
        for i in range(10):
            self.sock.sendto(rrq_packet(filename), server)
            logging.info("Waiting {} seconds for data".format(time / 1000))
            sleep(time / 1000)
            self.target, data = self.receive_data()
            if self.target is not None:
                return len(data) < 512, data
            else:
                time *= 1.2
        if self.target is None:
            raise ConnectionError("No response from the server")

    def file_error(self):
        pass


class ClientSender(Sender):
    def prepare(self, filename):
        self.block_id = 0
        server = self.target
        self.target = None
        time = 100
        for i in range(10):
            self.sock.sendto(wrq_packet(filename), server)
            logging.info("Waiting {} seconds for ACK".format(time/1000))
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