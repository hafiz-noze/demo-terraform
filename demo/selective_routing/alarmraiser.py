import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.exchange_declare(exchange='logs', exchange_type='direct')

result = channel.queue_declare(exclusive=True, queue="")
queue_name = result.method.queue

severity = ['info', 'warning', 'error']

channel.queue_bind(exchange='logs', queue=queue_name, routing_key='error')
channel.queue_bind(exchange='logs', queue=queue_name, routing_key='warning')

print(' [*] Waiting for logs. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(" [x] %r:%r" % (method.routing_key, body))

channel.basic_consume(on_message_callback=callback, queue=queue_name, auto_ack=True)
channel.start_consuming()