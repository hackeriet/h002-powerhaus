#!/usr/bin/env python
import sys, time
from socket import *

if __name__ == "__main__":
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    data = "input1=244 input2=0 input3=233 input4=1\n"
    while True:
        s.sendto(data, ('255.255.255.255', 1235))
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.5)
