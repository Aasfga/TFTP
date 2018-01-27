from tftp.abstract_workers.writer import *
from tftp.client import *
import time

from tftp.stopwatch import Stopwatch

logging.basicConfig(level=logging.DEBUG)
target = ("localhost", 6969)
receiver = ClientReceiver(target, MD5Writer)
stopwatch = Stopwatch()
receiver.receive_file = stopwatch.watch("receive_file", receiver.receive_file)
receiver.ask_for_data = stopwatch.watch("ask_for_data", receiver.ask_for_data)
receiver.receive_file("med_1.in")
print("Receive_file time: %.16f" % stopwatch.get_average("receive_file"))
print("Average time for one packet: %.16f" % stopwatch.get_average("ask_for_data"))


