'''
    @author SABINA 
    @created 07/03/2024 9:34 PM
    @project Backend Room Finder
'''

import pika
import json


class RabbitMQProducer:
    def __init__(self, rabbitmq_host, rabbitmq_port, exchange_name, queue_name, binding_key):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port))
        self.channel = self.connection.channel()

        # Declare the exchange
        self.channel.exchange_declare(exchange=exchange_name, exchange_type='topic')

        # Declare the queue with binding key
        self.channel.queue_declare(queue=queue_name)
        self.channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=binding_key)

    def send_message(self, message, routing_key, exchange):
        # Convert JSON data to a string
        json_message = json.dumps(message)

        # Send JSON data to the queue
        self.channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json_message.encode('utf-8'),  # Convert to byte string
            # body=message,  # Convert to byte string

            properties=pika.BasicProperties(
                delivery_mode=2,  # Make the message persistent
                )
            )
        print("Message sent to queue successsfully.")

    def close_connection(self):
        self.connection.close()
