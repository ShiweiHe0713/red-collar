import pika
import time
import zlib
import json
import requests
import _pickle as pickle
import logging
from mock_data import generate_order
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Configuration, current running on localhost
rabbitmq_host = "localhost"
exchange = "clothing_orders"
routing_key = "order_queue"

#Initialize publisher
publisher = RabbitMQOrderPublisher(rabbitmq_host, exchange, routing_key)

def send_order(order, retries=1):
    """Publish a single order to the rabbitmq"""
    try:
        for attempt in range(retries):
            try:
                local_publisher = RabbitMQOrderPublisher(rabbitmq_host, exchange, routing_key)
                local_publisher.publish_order(order)
                # TODO: sent to influxDB
                # local_publisher.close()
                return
            except Exception as e:
                time.sleep(2 ** attempt)
                publisher.logger.error(f"Error sending the order: {e}")
    except Exception as e:
        publisher.logger.error(f"Error calling the calling object: {e}")
    

# Concurrently generate and send orders
def send_orders_concurrently(num_orders):
    """Concurrently send multiple orders to the RabbitMQ"""

    orders = [generate_order() for _ in range(num_orders)]
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for order in orders:
            try:
                futures.append(executor.submit(send_order, order))
            except Exception as e:
                publisher.logger.error(f"Worder failed to send order: {e}")

        # futures = [executor.submit(send_order, order) for order in orders]
        for future in as_completed(futures):
            try:
                future.result()  # Ensure that we capture any exceptions raised during execution
            except Exception as e:
                publisher.logger.error(f"Errors in worker thread: {e}")

if __name__ == "__main__":
    # Generate and publish data
    try:
        send_orders_concurrently(2)
        
        # Nonconcurrent sending 
        # orders = [generate_order() for _ in range(2)]
        # for order in orders:
        #     send_order(order)
    except Exception as e:
        publisher.logger.error(f"Error in main: {e}")
    finally:
        publisher.close()