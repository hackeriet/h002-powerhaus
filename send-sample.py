#!/usr/bin/env python
import sys, time
import random
from socket import *
from pprint import pprint
from copy import copy

msg = ["powerhaus.hackeriet.no", "ticks/minute:",
       4.5, 12.1, 3.4, 0.0, 11.2, 23.32,
       "CTpower:",
       1234., 4321., 12315., 123., 0., 31213.]

def vary(msg):
    assert type(msg) == list
    newmsg = copy(msg)
    for i, item in enumerate(msg):
        if type(item) == float:
            _ = random.random() * item
            newmsg[i] = "%.3f" % _
    print newmsg
    return newmsg

# ticks/minute == LDR blinks, CTpower == current sensors.
if __name__ == "__main__":
    s = socket(AF_INET, SOCK_DGRAM)
    s.bind(('', 12345))
    s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
#    dest = ('255.255.255.255', 54321)
    dest = ('127.0.0.1', 54321)
    print "Sending samples to %s port %s." % dest

    while True:
        newmsg = " ".join(vary(msg))
        s.sendto(newmsg, dest)
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(2.0)
