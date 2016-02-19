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
    """
	Parse a powerhaus payload.

    >>> parse_packet("powerhaus0.hackeriet.no pulses/min: 30 0 570 0 0 0 CTpower: 1237.28 3805.76 4330.61 18152.15 1134.61 8167.95")
    [('p0', 30.0), ('p1', 0.0), ('p2', 570.0), ('p3', 0.0), ('p4', 0.0), ('ct0', 3805.76), ('ct1', 4330.61), ('ct2', 18152.15), ('ct3', 1134.61), ('ct4', 8167.95)]
"""
    l = payload.split(" ")

    if len(l) != 15:
        raise ParseError("Invalid number of fields (%i)" % len(l))

    if l[1] != "pulses/min:" or l[8] != "CTpower:":
        raise ParseError("Invalid packet")

    res = []
    try:
        for i in range(0, 5):
            tup = ("p%i" % i, float(l[2+i]))
            res += [tup]

        for i in range(0, 5):
            tup = ("ct%i" % i, float(l[10+i]))
            res += [tup]
    except ValueError as e:
        raise ParseError(e)
    
    return res

if __name__ == "__main__":
    unittest.main()
