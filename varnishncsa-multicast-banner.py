#!/usr/bin/env python

import thread
import socket
import struct
import sys
import subprocess

multicast_group = 'ff02::6789'
multicast_port = 10000;

def varnishban(host, url):
    #exitCode = subprocess.call(["varnishadm", "ban", "req.url == " + url + " && req.http.host == " + host])
    subprocess.Popen(["varnishadm", "ban", "req.url == " + url + " && req.http.host == " + host], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def multicast_sender(thread_name, group, port):
    addrinfo = socket.getaddrinfo(group, None)[0]

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
                print "Sending ban for " + host + uri
                sent = sock.sendto(message, (addrinfo[4][0], port))

    except (KeyboardInterrupt, SystemExit):
        raise

    finally:
        p.kill()
        sock.close()

def multicast_receiver(thread_name, group, port):
    addrinfo = socket.getaddrinfo(group, None)[0]
    sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(('', port))

    group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])

    if addrinfo[0] == socket.AF_INET:
        mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        mreq = group_bin + struct.pack('@I', 0)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    try:
        while True:
            data, sender = sock.recvfrom(1500)
            host, url = data.strip().split()
            print "Received ban for " + host + url
            varnishban(host, url)

    except (KeyboardInterrupt, SystemExit):
        raise

    finally:
        sock.close()

def main():
    try:
        thread.start_new_thread( multicast_sender, ("Listener", multicast_group, multicast_port))
        thread.start_new_thread( multicast_receiver, ("Thread-2", multicast_group, multicast_port))
    except:
        print "Error: unable to start thread"

    while 1:
        pass

if __name__ == '__main__':
    main()