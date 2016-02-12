#!/usr/bin/env python
"""
Powerhaus protocol implementation.

Author: Lasse Karstensen <lasse.karstensen@gmail.com>, February 2016.
"""
import random
import unittest
from datetime import datetime
from pprint import pprint
from sys import argv

class ParseError(Exception):
    pass

def parse_packet(payload):
    #powerhaus.hackeriet.no ticks/minute: 4.5 12.1 3.4 0.0 11.2 23.32 CTpower: 1234 4321 12315 123 0 31213
    l = payload.split(" ")

    if len(l) != 15:
        raise ParseError("Invalid number of fields (%i)" % len(l))

    if l[1] != "ticks/minute:" or l[8] != "CTpower:":
        raise ParseError("Invalid packet")

    res = [("ts", datetime.now())]
    try:
        for i in range(0, 5):
            tup = ("t%i" % i, float(l[2+i]))
            res += [tup]

        for i in range(0, 5):
            tup = ("p%i" % i, float(l[10+i]))
            res += [tup]
    except ValueError as e:
        raise ParseError(e)
    
    return res

class PowerhausTest(unittest.TestCase):
    def test_parse(self):
        res = parse_packet("powerhaus.hackeriet.no ticks/minute: 4.5 12.1 3.4 0.0 11.2 23.32 CTpower: 1234 4321 12315 123 0 31213")
        self.assertEqual(len(res), 11)

        self.assertEqual(res[1][0], "t0")
        self.assertEqual(res[1][1], 4.5)

        

if __name__ == "__main__":
    unittest.main()
