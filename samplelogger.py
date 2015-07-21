#!/usr/bin/env python
"""
A small server process that listens for UDP broadcast,
filters the incoming data and provide a JSON web service
with the results.

Used for graphing power usage.

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, February 2015.
"""
import threading
import json
import random
import socket
import BaseHTTPServer
import SocketServer

from datetime import datetime

import pcapy

from SocketServer import UDPServer, DatagramRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pprint import pprint, pformat
from sys import argv, stdout

# { "sensorid": [ 1.1, 1.2, 0.9, 1.1 ], }
readings = {}

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
    global readings
    print data
    # best check ever.
    if "zool" not in data:
        return
    ts = datetime.fromtimestamp(pkthdr.getts()[0])
    print "%s\t" % ts,
    sample = parse_sample(data)
    try:
        #print " ".join(["%s=%.3f" % (x[0], x[1]) for x in sample])
        print "\t".join(["%.2f" % (x[1]) for x in sample])
    except AttributeError:
        print "INVALID packet data: %s" % pformat(sample)
    stdout.flush()
#    pprint(sample)
       

class SampleHandler(DatagramRequestHandler):
    def handle(self):
        global readings
        payload = self.rfile.read()
        pprint(payload)

        for k in readings.keys():
            if len(readings[k]) > 20:
                readings[k].pop(0)

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass

    def do_GET(self):
        if (self.path == "/"):
            msg = "See /readings.json, please.\n"
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(msg))
            self.end_headers()
            self.wfile.write(msg)
        elif (self.path == "/readings.json"):
            body = json.dumps(readings, indent=4)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        else:
            msg = "400 Bad Request"
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

if __name__ == '__main__':
    if "-d" in argv:
        import daemon
        daemon.daemonize("/var/tmp/powerserver.pid")

    p = pcapy.open_live("eth0", 1500, False, 0)
    p.setfilter("udp and port 54321")
    p.loop(-1, pkt_cb)

    #us = UDPServer(("10.0.130.255", 54321), SampleHandler)
    #us = UDPServer(("10.0.130.255", 54321), SampleHandler)
    #us.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #t = threading.Thread(target=us.serve_forever)
    #t.setDaemon = True
    #t.start()

    BaseHTTPServer.allow_reuse_address = True
    SocketServer.TCPServer.address_family = socket.AF_INET6
    SocketServer.TCPServer.allow_reuse_address = True
    hp = ThreadedHTTPServer(("", 8088), HTTPRequestHandler)
    hp.serve_forever()
