import pika
import random

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='logs', exchange_type='direct')

severity = ['info', 'warning', 'error', 'other']
messages = ['EMsg', 'WMsg', 'IMsg', 'OMsg']

for i in range(10):
    randomNum = random.randint(0, len(severity)-1)
    print(randomNum)
    message = random.choice(messages)
    routing_key = severity[randomNum]
    channel.basic_publish(exchange='logs', routing_key=routing_key, body=message)
    print(" [x] Sent %r:%r" % (routing_key, message))

channel.exchange_delete(exchange='logs', if_unused=False)

connection.close()