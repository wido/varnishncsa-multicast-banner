#!/usr/bin/env python

import threading
import socket
import struct
import sys
import subprocess
import time

multicast_group = 'ff02::6789'
multicast_port = 10000;

keepRunning = True

def varnishban(host, url):
    subprocess.Popen(["varnishadm", "ban", "req.url == " + url + " && req.http.host == " + host], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def sendersocket(addr):
    addrinfo = socket.getaddrinfo(addr, None)[0]
    sock = socket.socket(addrinfo[0], socket.SOCK_DGRAM)
    ttl_bin = struct.pack('@i', 1)

    if addrinfo[0] == socket.AF_INET:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
    else:
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

    return sock

def receiversocket(addr, port):
    addrinfo = socket.getaddrinfo(addr, None)[0]
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

    return sock

def logmsg(name, message):
    print "[ %s ] [ %s ] %s" % (time.ctime(time.time()), name, message)

class mSenderThread(threading.Thread):
    def __init__(self, threadID, name, group, port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.group = group
        self.port = port
        self.name = name
 
    def run(self):
        logmsg(self.name, "Sending on multicast group %s:%s" % (self.group, self.port))
        sock = sendersocket(self.group)

        try:
            p = subprocess.Popen(['/usr/bin/varnishncsa', '-F', '%m %{Host}i %U'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while keepRunning:
                retcode = p.poll()
                line = p.stdout.readline().strip()
                method, host, uri = line.split()
                if (method == "PUT") or (method == "DELETE"):
                    message = host + " " + uri
                    logmsg(self.name, "Sending ban for %s%s" %  (host, uri))
                    sent = sock.sendto(message, (self.group, self.port))

        except (KeyboardInterrupt, SystemExit):
            raise

        finally:
            p.kill()
            sock.close()

class mReceiverThread(threading.Thread):
    def __init__(self, threadID, name, group, port):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.group = group
        self.port = port
        self.name = name

    def run(self):
        logmsg(self.name, "Listening on multicast group %s:%s" % (self.group, self.port))
        sock = receiversocket(self.group, self.port)

        try:
            while keepRunning:
                data, sender = sock.recvfrom(1500)
                host, uri = data.strip().split()
                logmsg(self.name, "Received ban for %s%s" %  (host, uri))
                varnishban(host, uri)

        except (KeyboardInterrupt, SystemExit):
            raise

        finally:
            sock.close()

def main():
    print "[Main] Starting threads"
    sender = mSenderThread(1, "Listener", multicast_group, multicast_port)
    receiver = mReceiverThread(2, "Banner", multicast_group, multicast_port)

    sender.start()
    receiver.start()
    while 1:
        try:
            pass
        except (KeyboardInterrupt, SystemExit):
            raise
        finally:
            keepRunning = False
            break

if __name__ == '__main__':
    main()