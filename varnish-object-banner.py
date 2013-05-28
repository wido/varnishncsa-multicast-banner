#!/usr/bin/env python
import pika
import json
from subprocess import call

def callback(ch, method, properties, body):
    fields = body.split(" ")
    exitCode = call(["varnishadm", "ban", "req.url == " + fields[1] + " && req.http.host == " + fields[0]]) 

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.exchange_declare(exchange='radosgw', type='fanout')

result = channel.queue_declare(exclusive=True)
queue_name = result.method.queue

channel.queue_bind(exchange='radosgw', queue=queue_name)

channel.basic_consume(callback, queue=queue_name, no_ack=True)

channel.start_consuming()
