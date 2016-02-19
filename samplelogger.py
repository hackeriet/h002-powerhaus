#!/usr/bin/env python
"""
A small pcap service that listens for the malformed UDP broadcasts
sent by the power monitor, and writes a data file to disk.

Used for graphing power usage.

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, July 2015.
"""

import os
import json
import sys
from datetime import datetime
from pprint import pprint, pformat
import pcapy

from powerhaus import *

outputfp = None

def pkt_cb(pkthdr, data):
    assert outputfp is not None

    # best check ever.
    if "powerhaus0.hackeriet.no" not in data:
        return

    ts = datetime.fromtimestamp(pkthdr.getts()[0])
    try:
        sample = parse_packet(data[42:])
        #print " ".join(["%s=%.3f" % (x[0], x[1]) for x in sample])
        outputfp.write("%s\t" % ts)
        outputfp.write("\t".join(["%.2f" % (x[1]) for x in sample]) + "\n")
    except AttributeError:
        outputfp.write("%s\t" % ts)
        outputfp.write("INVALID packet data: %s\n" % pformat(sample))
    outputfp.flush()

def handle(self):
    global readings
    payload = self.rfile.read()
    for k in readings.keys():
        if len(readings[k]) > 20:
            readings[k].pop(0)


if __name__ == '__main__':
    if os.geteuid() != 0:
        print >>sys.stderr, "ERROR: Need to be root to run pcap."
        exit(1)

    outputfp = sys.stdout
    if len(sys.argv) > 1:
        outputfp = open(sys.argv[1], "a")

    p = pcapy.open_live("eno1", 1500, True, 0)
    p.setfilter("udp and port 54321")

    if 1:
        os.setgid(65534)
        os.setgroups([])
        os.setuid(65534)

    p.loop(-1, pkt_cb)
