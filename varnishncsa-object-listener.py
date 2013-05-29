#!/usr/bin/env python

import pika
import os
import sys
import subprocess

def varnishncsa_reader():
    p = subprocess.Popen(['/usr/bin/varnishncsa', '-F', '%m %{Host}i %U'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while(True):
        retcode = p.poll()
        line = p.stdout.readline().strip()
        line_processor(line)

def line_processor(line):
    method, host, uri = line.split()
    if (method == "PUT") or (method == "DELETE"):
        message = host + " " + uri
        channel.basic_publish(exchange='radosgw',
                  routing_key='',
                  body=message)

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.exchange_declare(exchange='radosgw', type='fanout')

varnishncsa_reader()

connection.close()
