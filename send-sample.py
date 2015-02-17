#!/usr/bin/env python
import sys, time
from socket import *

if __name__ == "__main__":
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    dest = ('255.255.255.255', 1235)
    print "Sending samples to %s port %s." % dest
    data = "input1=244 input2=0 input3=233 input4=1\n"
    while True:
        s.sendto(data, dest)
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.5)
