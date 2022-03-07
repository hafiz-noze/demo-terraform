import puka
import time
import random
import datetime

producer = puka.Client()
connect_promise = producer.connect('amqp://user:PASSWORD@localhost:5672/%2f')
producer.wait(connect_promise)

exchange_promise = producer.exchange_declare(exchange='newsletter', type='fanout')
producer.wait(exchange_promise)

while True:
    message = '{} - {}'.format(datetime.datetime.now(), random.randint(1, 1000))
    print('Sending message: {}'.format(message))
    producer.basic_publish(exchange='newsletter', routing_key='', body=message)
    time.sleep(1)
producer.close() 