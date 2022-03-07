# Import python AMQP client library
import pika

# Create a connection to the AMQP server, say CN
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
# Create a channel, say CH
channel = connection.channel()

# create a queuse through default exchange
channel.queue_declare(queue='hello')

# publish a message to the queue
channel.basic_publish(exchange='', routing_key='hello', body='Hello World! msg#1')
print(" [x] Sent 'Hello World!'")

# Close the connection
connection.close()