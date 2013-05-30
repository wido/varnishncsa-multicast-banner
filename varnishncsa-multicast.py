#!/usr/bin/env python

import socket
import struct
import sys
import subprocess

multicast_group = 'ff02::6789'
multicast_port = 10000;

addrinfo = socket.getaddrinfo(multicast_group, None)[0]

sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

ttl_bin = struct.pack('@i', 1)

if addrinfo[0] == socket.AF_INET:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
else:
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

try:
    p = subprocess.Popen(['/usr/bin/varnishncsa', '-F', '%m %{Host}i %U'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll()
        line = p.stdout.readline().strip()
        method, host, uri = line.split()
        if (method == "PUT") or (method == "DELETE"):
            message = host + " " + uri
            print "Sending ban: " + message
            sent = sock.sendto(message, (addrinfo[4][0], multicast_port))

finally:
    print >>sys.stderr, 'closing socket'
    sock.close()