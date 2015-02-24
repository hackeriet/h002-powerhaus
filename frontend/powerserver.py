#!/usr/bin/env python
import threading
import datetime
import json
import random
import socket

from SocketServer import UDPServer, DatagramRequestHandler
from SimpleHTTPServer import SimpleHTTPRequestHandler
from pprint import pprint
import BaseHTTPServer
import SocketServer
#from SocketServer import ThreadedHTTPServer

# { "sensorid": [ 1.1, 1.2, 0.9, 1.1 ], }
readings = {}

class SampleHandler(DatagramRequestHandler):
    def handle(self):
        global readings
        #pprint(readings)
        payload = self.rfile.read()
        for sensor in payload.split():
            name, value = sensor.split("=")
            try:
                readings[name] += [value]
            except:
                readings[name] = [value]

            if len(readings[name]) > 20:
                readings[name].pop(0)

class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if (self.path == "/"):
            msg = "OK"
            #return render_template('front.html', **res)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.send_header("Content-Length", len(msg))
            self.end_headers()
            self.wfile.write(msg)
        elif (self.path == "/readings.json"):
            body = json.dumps(readings, indent=2)
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
        pass
        if 0:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    us = UDPServer(("0.0.0.0", 1235), SampleHandler)
    t = threading.Thread(target=us.serve_forever)
    t.setDaemon = True
    t.start()

    BaseHTTPServer.allow_reuse_address = True
    SocketServer.TCPServer.address_family = socket.AF_INET6
    SocketServer.TCPServer.allow_reuse_address = True
    hp = ThreadedHTTPServer(("", 8080), HTTPRequestHandler)
    hp.serve_forever()
