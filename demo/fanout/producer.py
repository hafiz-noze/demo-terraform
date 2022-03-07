# Import python AMQP client library
import pika

# Create a connection to the AMQP server, say CN
connection = pika.BlockingConnection(pika.ConnectionParameters())
# Create a channel, say CH
channel = connection.channel()

# Create the exchange (will not effect if exchange already exists)
channel.exchange_declare(exchange='logs', exchange_type='fanout')

for i in range(10):
    # Create a message
    message = 'Message #{}'.format(i)
    # Publish the message
    channel.basic_publish(exchange='logs', routing_key='', body=message)
    print(' [x] Sent {}'.format(message))

channel.exchange_delete(exchange='logs', if_unused=False)

# Close the connection
connection.close()