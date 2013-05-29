#!/usr/bin/env python

import socket
import struct
import sys
import subprocess

multicast_group = ('224.3.29.71', 10000)

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set a timeout so the socket does not block indefinitely when trying
# to receive data.
sock.settimeout(0.2)

# Packets are not allowed to pass a router
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    p = subprocess.Popen(['/usr/bin/varnishncsa', '-F', '%m %{Host}i %U'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll()
        line = p.stdout.readline().strip()
        method, host, uri = line.split()
        if (method == "PUT") or (method == "DELETE"):
            message = host + " " + uri
            sent = sock.sendto(message, multicast_group)

finally:
    print >>sys.stderr, 'closing socket'
    sock.close()