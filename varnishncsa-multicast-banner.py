#!/usr/bin/env python

import socket
import struct
import sys
from subprocess import call

def varnishban(host, url):
    exitCode = call(["varnishadm", "ban", "req.url == " + url + " && req.http.host == " + host])

multicast_group = '224.3.29.71'
server_address = ('', 10000)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    data, address = sock.recvfrom(1024)
    host, url = data.split()
    print "Banning " + host + url
    varnishban(host,url)