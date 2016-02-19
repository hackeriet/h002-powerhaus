#!/usr/bin/env python
"""
A small server process that listens for UDP broadcast,
filters the incoming data and provide a JSON web service
with the results.

Used for graphing power usage.

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, February 2015.
"""

import sys
import os
import datetime
import json
import logging
import random
import socket
import pcapy
#import multiprocessing
from multiprocessing import Process
from datetime import datetime
from pprint import pprint, pformat
from os.path import join, dirname, realpath, basename
import BaseHTTPServer
import SocketServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

import powerhaus

# { "sensorid": [ 1.1, 1.2, 0.9, 1.1 ], }
readings = {}

# https://docs.python.org/2/library/multiprocessing.html -> Shared Memory
#    arr = Array('i', range(10))

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if (self.path == "/"):
            self.path = "/index.html"
        elif (self.path == "/readings.json"):
            body = json.dumps(readings, indent=2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        filename = join(dirname(realpath(__file__)), "htdocs", self.path[1:])
        try:
            fileinfo = stat(filename)
        except Exception:  # XXX
            fileinfo = None

        if fileinfo:
            body = open(filename).read()

            if filename.endswith(".html"):
                mime = "text/html"
            elif filename.endswith(".js"):
                mime = "application/javascript"
            elif filename.endswith(".css"):
                mime = "application/css"
            else:
                mime = "text/plain"

            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            msg = "400 Bad Request\n"
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(msg))
            self.end_headers()
            self.wfile.write(msg)

class ThreadedHTTPServer(SocketServer.ThreadingMixIn,
                         BaseHTTPServer.HTTPServer):
    """Handle requests in a separate thread."""

    def handle_error(self, request, client_address):
        if 0:
            import traceback
            traceback.print_exc()


def PcapRunner(interface="eno1"):
    p = pcapy.open_live(interface, 1500, True, 0)
    p.setfilter("udp and port 54321")
    if True:
        os.setgid(65534)
        os.setgroups([])
        os.setuid(65534)
    print "Done initing .."
    p.loop(-1, pkt_cb)
    print "mjoff .. "

def pkt_cb(pkthdr, data):
    assert os.geteuid() != 0

    # best check ever.
    if "powerhaus0.hackeriet.no" not in data:
        return

    outputfp = sys.stdout
    ts = datetime.fromtimestamp(pkthdr.getts()[0])
    try:
        sample = powerhaus.parse_packet(data[42:])
        #print " ".join(["%s=%.3f" % (x[0], x[1]) for x in sample])
        outputfp.write("%s\t" % ts)
        outputfp.write("\t".join(["%.2f" % (x[1]) for x in sample]) + "\n")
    except AttributeError:
        outputfp.write("%s\t" % ts)
        outputfp.write("INVALID packet data: %s\n" % pformat(sample))

    for k, v in sample[1:]:
        if not k in readings:
            readings[k] = [v]
            return

        if len(readings[k]) == 3:
            readings[k].pop(0)
        readings[k] += [v]
    logging.debug("state: %s" % pformat(readings))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if os.geteuid() != 0:
        logging.error("Need to be root to run pcap")
        exit(1)

    source = Process(target=PcapRunner, args=[])
    source.start()

    if 1:
        BaseHTTPServer.allow_reuse_address = True
        SocketServer.TCPServer.address_family = socket.AF_INET6
        SocketServer.TCPServer.allow_reuse_address = True
        hp = ThreadedHTTPServer(("", 8088), HTTPRequestHandler)

        try:
            hp.serve_forever()
        except KeyboardInterrupt:
            pass

    print "waiting for pcap .."
    source.join()
