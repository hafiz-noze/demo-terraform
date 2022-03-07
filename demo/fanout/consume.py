import pika

# Create a connection to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))

# Create a channel
channel = connection.channel()

# Create the exchange (will not effect if excchange already exists)
channel.exchange_declare(exchange='logs', exchange_type='fanout')

# Create the temporary queue, if it does not already exist and associate it with the channel exclusively
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
print("Queue name: %r" % queue_name)

# Bind the queue to the exchange
channel.queue_bind(exchange='logs', queue=queue_name)
print(' [*] Waiting for logs. To exit press CTRL+C')

# Create a function to handle messages
def callback(ch, method, properties, body):
    print(" [x] %r" % body)

channel.basic_consume(callback, queue=queue_name, auto_ack=True)

channel.start_consuming()