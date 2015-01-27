#!/usr/bin/env python
# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, jsonify

import threading
import datetime
import json
import random

from SocketServer import UDPServer, DatagramRequestHandler
from pprint import pprint

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# { "sensorid": [ 1.1, 1.2, 0.9, 1.1 ], }
readings = {
    "sensor1": [ 1.1, 1.2, 0.9, 1.1 ],
    "sensor2": [ 1.1, 1.2, 0.9, 1.1 ],
    "sensor3": [ 1.1, 1.2, 0.9, 1.1 ],
}

class SampleHandler(DatagramRequestHandler):
    def handle(self):
        print dir(self)
        print self.rfile.readline().strip()

class UDPListener(threading.Thread):
    def run(self):
        self.samplereader = UDPServer(("0.0.0.0", 1234), SampleHandler)
        print "Starting UDP server."
        self.samplereader.serve_forever()

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

@app.route('/')
def index():
    res = {}
    res["readings"] = readings
    res["now"] = datetime.datetime.now()
#    res["classes"] = sorted(list(set([ x["class"] for x in d.values()])))
    return render_template('front.html', **res)

@app.route('/readings.json')
def readings_endpoint():
    global readings
    readings["sensor1"] += [2 * random.random()]
    readings["sensor2"] += [1 + 1 * random.random()]
    readings["sensor3"] += [2 * random.random()]
    for k, v in readings.items():
        if len(v) > 20:
            readings[k].pop(0)
    return jsonify(**readings)

if __name__ == '__main__':
    if 0:
        ul = UDPListener().start()
    app.run(host="0.0.0.0", debug=True)
