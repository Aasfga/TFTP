def rrq_packet(filename):
    return (1).to_bytes(2, "big") + filename.encode() + "\x00octet\x00".encode()


def wrq_packet(filename):
    return (2).to_bytes(2, "big") + filename.encode() + "\x00octet\x00".encode()


def data_packet(block, data):
    return (3).to_bytes(2, "big") + block.to_bytes(2, "big") + data


def ack_packet(block):
    return (4).to_bytes(2, "big") + block.to_bytes(2, "big")


def error_packet(error_code, msg):
    return (5).to_bytes(2, "big") + error_code.to_bytes(2, "big") + msg.encode() + "\x00".encode()


def parse_request(packet):
    return packet[2:-7].decode()


def parse_rrq(packet):
    return parse_request(packet)


def parse_wrq(packet):
    return parse_request(packet)


def parse_data(packet):
    block = packet[2:4]
    data = packet[4:]
    return int.from_bytes(block, "big"), data


def parse_ack(packet):
    return int.from_bytes(packet[2:4], "big")


def parse_error(packet):
    error_code = packet[2:4]
    error_msg = packet[4:-1]
    return int.from_bytes(error_code, "big"), error_msg.decode()


def parse_packet(packet):
    op_code = int.from_bytes(packet[:2], "big")
    if op_code == 1:
        parse = parse_rrq
    elif op_code == 2:
        parse = parse_wrq
    elif op_code == 3:
        parse = parse_data
    elif op_code == 4:
        parse = parse_ack
    elif op_code == 5:
        parse = parse_error
    else:
        raise ValueError
    return op_code, parse(packet)
