#!/usr/bin/env python
"""
A small server process that listens for UDP broadcast,
filters the incoming data and provide a JSON web service
with the results.

Used for graphing power usage.

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, February 2015.
"""
import datetime
import json
import logging
import random
import socket
import threading

import BaseHTTPServer
import SocketServer

from SocketServer import UDPServer, DatagramRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pprint import pprint, pformat
from sys import argv
from os import stat
from os.path import join, dirname, realpath, basename

import powerhaus

# { "sensorid": [ 1.1, 1.2, 0.9, 1.1 ], }
readings = {}

class SampleHandler(DatagramRequestHandler):
    def handle(self):
        global readings
        payload = self.rfile.read()
        try:
            sample = powerhaus.parse_packet(payload)
        except powerhaus.ParseError as e:
            logging.debug("Invalid packet received. Error: %s" % str(e))
            return

        for k, v in sample[1:]:
            if not k in readings:
                readings[k] = [v]
                return

            if len(readings[k]) == 3:
                readings[k].pop(0)
            readings[k] += [v]
        #logging.debug("state: %s" % pformat(readings))

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    #def log_message(self, *args, **kwargs):
    #    pass

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

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    us = UDPServer(("", 54321), SampleHandler)
    t = threading.Thread(target=us.serve_forever)
    t.setDaemon = True
    t.start()

    BaseHTTPServer.allow_reuse_address = True
    SocketServer.TCPServer.address_family = socket.AF_INET6
    SocketServer.TCPServer.allow_reuse_address = True

    httpport = argv[1] if len(argv) > 1 else 8088
    hp = ThreadedHTTPServer(("", httpport), HTTPRequestHandler)
    hp.serve_forever()
