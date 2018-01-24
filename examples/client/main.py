from tftp.abstract_workers.receiver import ClientReceiver
from tftp.abstract_workers.writer import *

target = ("localhost", 6969)
# cs = ClientSender(target)
# cs.send_file("big_file.txt")
cr = ClientReceiver(target, PrintWriter)
cr.receive_file("small_file.txt")
# sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# sock.sendto(data_packet(1000, "Hello World!"), target)
# sock.sendto(error_packet(123, "FILE_NAME"), target)
# sock.sendto(rrq_packet("abc.txt"), target)
# c = Client("localhost")
# c._send_ack(5)
# i = 10010
# b = i.to_bytes(2, byteorder="big")
# n = 0
# for byte in b:
#     n *= 256
#     n += byte
# print(n)
# wc = WriteClient(target)
# wc.write("big_file.txt")
