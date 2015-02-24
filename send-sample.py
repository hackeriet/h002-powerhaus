#!/usr/bin/env python
import sys, time
from socket import *

if __name__ == "__main__":
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
    dest = ('255.255.255.255', 1235)
    print "Sending samples to %s port %s." % dest

    #powerhaus.hackeriet.no ticks/minute: 4.5 12.1 3.4 0.0 11.2 23.32 CTpower: 1234 4321 12315 123 0 31213
    ticksamples = "4.5 12.1 3.4 0.0 11.2 23.32".split()  # LDR blinks.
    powersamples = "1234 4321 12315 123 0 31213".split()  # current sensors

    while True:
        msg = ["powerhaus.hackeriet.no"]
        msg += ["ticks/minute: "] + ticksamples
        msg += ["TPower:"] + powersamples
        s.sendto(" ".join(msg), dest)
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2.0)
