#!/usr/bin/env python
import sys, time
import random
from socket import *
from pprint import pprint

if __name__ == "__main__":
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 12345))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
#    dest = ('255.255.255.255', 54321)
    dest = ('10.0.130.255', 54321)
    print "Sending samples to %s port %s." % dest

    #powerhaus.hackeriet.no ticks/minute: 4.5 12.1 3.4 0.0 11.2 23.32 CTpower: 1234 4321 12315 123 0 31213
    ticksamples = "4.5 12.1 3.4 0.0 11.2 23.32".split()  # LDR blinks.
    powersamples = "1234 4321 12315 123 0 31213".split()  # current sensors
    powersamples = [ float(x) for x in powersamples ]

    pprint(powersamples)
    powersamples = [random.random() * x for x in powersamples]
    powersamples = [ "%.3f" % x for x in powersamples ]

    while True:
        msg = ["powerhaus.hackeriet.no"]
        msg += ["ticks/minute: "] + ticksamples
        msg += ["TPower:"] + powersamples
        s.sendto(" ".join(msg), dest)
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2.0)
