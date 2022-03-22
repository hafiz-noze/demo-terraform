import pika
import time
import datetime
import json
import sys

queue =  "all_messages"

credentials = pika.PlainCredentials('user', 'PASSWORD')
connection = pika.BlockingConnection(
pika.ConnectionParameters("rabbitmq-headless.keda", 5672, '/', credentials)) 
channel = connection.channel()

channel.exchange_declare(exchange='all_message', exchange_type='direct')
channel.queue_declare(queue=queue, durable=True, arguments={"x-queue-type": "quorum"})


channel.queue_bind(exchange='all_message', queue=queue, routing_key='error')
channel.queue_bind(exchange='all_message', queue=queue, routing_key='info')

def callback(ch, method, body):
    print(" [x] Received {}".format(body))
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue=queue, auto_ack=True)

channel.start_consuming()