#!/usr/bin/env python

import socket
import time

MCAST_GRP = '239.255.13.37'
MCAST_PORT = 1234

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    while True:
        sock.sendto("foo at %s" % time.time(), (MCAST_GRP, MCAST_PORT))
        time.sleep(1)

