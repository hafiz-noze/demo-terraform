import puka

consume = puka.Client()
connect_promise = consume.connect('amqp://user:PASSWORD@localhost:5672/%2f')
consume.wait(connect_promise)

queue_promise = consume.queue_declare(exclusive=True)
queue = consume.wait(queue_promise)['queue']

bind_promise = consume.queue_bind(exchange='newsletter', queue=queue)
consume.wait(bind_promise)


message_promise = consume.basic_consume(queue=queue, no_ack=True)
while True:
    message = consume.wait(message_promise)
    print('Received message: {}'.format(message['body']))

consume.close()

