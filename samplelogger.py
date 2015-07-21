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

outputfp = None

def parse_sample(payload):
    """
    Parse a powerhaus data sample, like this:

    >>> parse_sample("preamble powerhaus0.kakesmurf.zool pulses/min: 570 570 210 360 330 1110 CTpower: 162.17 4527.03 4579.05 4293.94 2320.26 1415.14")
    [('b1', 570.0), ('b2', 570.0), ('b3', 210.0), ('b4', 360.0), ('b5', 330.0), ('b6', 1110.0), ('ct1', 162.17), ('ct2', 4527.03), ('ct3', 4579.05), ('ct4', 4293.94), ('ct5', 2320.26), ('ct6', 1415.14)]
    """
    l = payload.split(" ")
    if len(l) != 16:
        return
    blinks = l[3:9]
    ctpower = l[10:16]

    r = []
    for i, value in enumerate(blinks):
        name = "b%i" % (i+1)
        r += [(name, float(value))]

    for i, value in enumerate(ctpower):
        name = "ct%i" % (i+1)
        r += [(name, float(value))]
    return r

def pkt_cb(pkthdr, data):
    assert outputfp is not None

    # best check ever.
    if "zool" not in data:
        return
    ts = datetime.fromtimestamp(pkthdr.getts()[0])
    try:
        sample = parse_sample(data)
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
    pprint(payload)
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

    p = pcapy.open_live("eth0", 1500, True, 0)
    p.setfilter("udp and port 54321")
    p.loop(-1, pkt_cb)
