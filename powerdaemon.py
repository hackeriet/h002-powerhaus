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
import json
import logging
import socket
from time import time, sleep
from threading import Thread
from datetime import datetime
from pprint import pprint, pformat
from os.path import join, dirname, realpath, basename
import BaseHTTPServer
import SocketServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
import pcapy

import powerhaus

global readings, shutdown
readings = {}
shutdown = False


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

    # Drop privileges now that we're done binding.
    os.setgid(65534)
    os.setgroups([])
    os.setuid(65534)

    while shutdown is False:
        p.dispatch(0, pkt_cb)

def pkt_cb(pkthdr, data):
    assert os.geteuid() != 0
    global readings

    # best check ever.
    if "powerhaus0.hackeriet.no" not in data:
        return

    ts = datetime.fromtimestamp(pkthdr.getts()[0])

    try:
        sample = powerhaus.parse_packet(data[42:])
    except AttributeError:
        logging.debug("INVALID packet data: %s\n" % pformat(sample))
        return

    for k, v in sample:
        if k not in readings:
            readings[k] = []
        readings[k].append(v)
        if len(readings[k]) == 15:
            readings[k].pop(0)
    #logging.debug("state: %s" % pformat(readings))

def FileSnapshot(outputfile="/var/tmp/powerhaus.json"):
    assert os.geteuid() != 0
    global readings

    last_write = 0.0
    while shutdown is False:
        if last_write < time() - 60:
            last_write = time()
            # blatantly ignoring the possiblity of overwriting something ..
            with open(outputfile, "w+") as fp:
                fp.write(json.dumps(readings, indent=2))
        sleep(0.2)

def WebServer(port=8088):
    assert os.geteuid() != 0
    global readings, shutdown

    BaseHTTPServer.allow_reuse_address = True
    SocketServer.TCPServer.address_family = socket.AF_INET6
    SocketServer.TCPServer.allow_reuse_address = True
    hp = ThreadedHTTPServer(("127.0.0.1", port), HTTPRequestHandler)

    while shutdown is False:
        # This blocks until the next request comes along ...
        hp.handle_request()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if os.geteuid() != 0:
        logging.error("Need to be root to run this program. (pcap)")
        exit(1)

    logging.info("Starting up..")
    source = Thread(target=PcapRunner, args=[])
    source.start()
    filewriter = Thread(target=FileSnapshot, args=[])
    filewriter.start()
    httpserver = Thread(target=WebServer, args=[])
    httpserver.start()

    while shutdown is False:
        try:
            sleep(0.2)
        except KeyboardInterrupt:
            shutdown = True
            break

    logging.debug("Shutting down..")
    filewriter.join()
    source.join()
    httpserver.join()

    logging.info("Normal exit")
