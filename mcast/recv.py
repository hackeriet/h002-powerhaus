#!/usr/bin/env python

import socket
import struct

if __name__ == "__main__":
    interface_ip = "10.0.130.100"  # hardcoded :-)
    mgroup = "239.255.13.37"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((mgroup, 1234))
    s.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF,
                 socket.inet_aton(interface_ip))

    mreq = struct.pack('4sl', socket.inet_aton(mgroup), socket.INADDR_ANY)
    s.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        print s.recv(1024)

