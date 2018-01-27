import socket
import time
import math
from tftp.packet import *


class Worker:
    UDP_SIZE = 65527
    START_TIME = 0.1
    MAX_TIME = 100
    CHANGE = 1
    ROUNDS = int(round(math.log(MAX_TIME / START_TIME + 1, 2) - 1))

    def prepare(self, filename):
        raise NotImplementedError

    def __init__(self, target):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.block = None
        self.data_size = 1024
        self.window_size = 1
        if target[0] == "localhost":
            target = "127.0.0.1", target[1]
        self.target = target

    def block_add(self, x):
        return (self.block + x) % 2 ** 16

    def receive_packet(self, wait_time):
        self.sock.settimeout(wait_time)
        begin = time.time()
        packet = self.sock.recvfrom(Worker.UDP_SIZE)
        return packet, wait_time - (time.time() - begin)

    def send_error(self, code, msg):
        self.sock.sendto(error_packet(code, msg), self.target)
