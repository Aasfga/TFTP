from tftp.client import *

# logging.basicConfig(level=logging.DEBUG)
target = ("localhost", 6969)
cs = ClientSender(target)
cs.send_file("small_file.txt")
cs = ClientSender(target)
cs.send_file("big_file.txt")
# cr = ClientReceiver(target, FileWriter)
# cr.receive_file("big_file.txt")
