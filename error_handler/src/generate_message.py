import pika
import time
import random
import json
import datetime

count = 10000
#queue = 'all_message'

credentials = pika.PlainCredentials('user', 'PASSWORD')
connection = pika.BlockingConnection(
pika.ConnectionParameters("rabbitmq-headless.keda", 5672, '/', credentials)) 
channel = connection.channel()
#channel.queue_declare(queue=queue, durable=True, arguments={"x-queue-type": "quorum"})
channel.exchange_declare(exchange='all_message', exchange_type='direct')

for i in range(1, count+1):
    if i % 5 == 0:
        rk = 'error'
        message = {
            "id": i,
            "message": "Error Message {}".format(i),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    else:
        rk = 'info'
        message = {
            "id": i,
            "message": "Hey buddy, we are doing good {}".format(i),
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    channel.basic_publish(exchange='all_message', routing_key=rk, body=json.dumps(message))
    print(" [x] Sent {}".format(message))
    time.sleep(random.randint(1, 3))

channel.exchange_declare(exchange='error_message', if_unused=False)
connection.close()
