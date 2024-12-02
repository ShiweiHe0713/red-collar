import pika
import zlib
import json
import _pickle as pickle
import logging
from mock_data import generate_order

class RabbitMQOrderPublisher:
    def __init__(self, rabbitmq_host, exchange, routing_key):
        self.rabbitmq_host = rabbitmq_host
        self.exchange = exchange
        self.routing_key = routing_key
        self.connection = None
        self.channel = None
        self.setup_logging()
        self.connect()

    def setup_logging(self):
        LOG_LEVEL = logging.INFO
        LOG_FILE = "clothing_order_publisher.log"
        self.logger = logging.getLogger(LOG_FILE)
        self.logger.setLevel(LOG_LEVEL)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s: clothing_order_publisher: %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(LOG_LEVEL)
        self.logger.addHandler(stream_handler)
        self.logger.propagate = False

    def connect(self):
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbitmq_host))
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, exchange_type='direct')
            self.logger.info(f"Connected to RabbitMQ at {self.rabbitmq_host}")
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def publish_order(self, order_data):
        try:
            compressed_data = json.dumps(order_data)
            self.channel.basic_publish(exchange=self.exchange, routing_key=self.routing_key, body=compressed_data)
            self.logger.info(f"Published order: {order_data}")
        except Exception as e:
            self.logger.error(f"Failed to publish order: {e}")

    def close(self):
        if self.connection:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed")

if __name__ == "__main__":
    # Configuration, current running on localhost
    rabbitmq_host = "localhost"
    exchange = "clothing_orders"
    routing_key = "order_queue"

    #Initialize publisher
    publisher = RabbitMQOrderPublisher(rabbitmq_host, exchange, routing_key)

    # Generate and publish data
    for _ in range(1):
        order = generate_order()
        publisher.publish_order(order)

    # Close the connection when finish publishing
    publisher.close()