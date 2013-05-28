#!/usr/bin/env python

import pika
import os
import sys
import subprocess

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.exchange_declare(exchange='radosgw', type='fanout')

p = subprocess.Popen(['/usr/bin/varnishncsa', '-F', '%m %{Host}i %U'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
while(True):
    retcode = p.poll()
    line = p.stdout.readline().strip()
    fields = line.split(" ")
    if (fields[0] == "PUT") or (fields[0] == "DELETE"):
        message = fields[1] + " " + fields[2]
        channel.basic_publish(exchange='radosgw',
                      routing_key='',
                      body=message)

connection.close()
