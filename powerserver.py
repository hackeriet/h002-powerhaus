#!/usr/bin/env python
"""
A small server process that listens for UDP broadcast,
filters the incoming data and provide a JSON web service
with the results.

Used for graphing power usage.

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, February 2015.
"""
import threading
import datetime
import json
import random
import socket
import BaseHTTPServer
import SocketServer

from SocketServer import UDPServer, DatagramRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pprint import pprint
from sys import argv

# { "sensorid": [ 1.1, 1.2, 0.9, 1.1 ], }
readings = {}

class SampleHandler(DatagramRequestHandler):
    def handle(self):
        global readings
        payload = self.rfile.read()
        #powerhaus.hackeriet.no ticks/minute: 4.5 12.1 3.4 0.0 11.2 23.32 CTpower: 1234 4321 12315 123 0 31213
        l = payload.split(" ")
        if len(l) != 16:
            return
        ticks = l[3:9]
        tpow = l[10:16]
        for i, value in enumerate(ticks):
            name = "t%i" % i
            try:
                readings[name] += [value]
            except:
                readings[name] = [value]

        for i, value in enumerate(tpow):
            name = "p%i" % i
            try:
                readings[name] += [value]
            except:
                readings[name] = [value]

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

    us = UDPServer(("", 1235), SampleHandler)
    t = threading.Thread(target=us.serve_forever)
    t.setDaemon = True
    t.start()

    BaseHTTPServer.allow_reuse_address = True
    SocketServer.TCPServer.address_family = socket.AF_INET6
    SocketServer.TCPServer.allow_reuse_address = True
    hp = ThreadedHTTPServer(("", 8088), HTTPRequestHandler)
    hp.serve_forever()
