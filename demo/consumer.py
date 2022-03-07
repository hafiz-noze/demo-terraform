import pika, sys, os

def main():
    # Create a connection to the AMQP server, say CN
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    # Create a channel, say CH
    channel = connection.channel()
    # create a queue through default exchange
    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        print(" [x] Received %r" % body)
    
    # associate a callback function with the queue
    channel.basic_consume(on_message_callback=callback, queue='hello', auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
