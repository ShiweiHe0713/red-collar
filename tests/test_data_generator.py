import unittest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor
from data_generator.publish_to_rabbitmq import RabbitMQOrderPublisher, send_orders_concurrently, generate_order

class TestConcurrentOrderPublishing(unittest.TestCase):

    @patch('data_generator.publish_to_rabbitmq.RabbitMQOrderPublisher')
    def test_concurrent_data_sending(self, MockRabbitMQOrderPublisher):
        """
        Test concurrent order generation and sending.
        """
        # Mock the RabbitMQ publisher
        mock_publisher = MockRabbitMQOrderPublisher.return_value
        mock_publisher.publish_order = MagicMock()
        
        # Number of orders to generate and send
        num_orders = 10
        
        # Run the concurrent order sending
        with patch('data_generator.publish_to_rabbitmq.generate_order') as mock_generate_order:
            # Mock generate_order to return a consistent result
            mock_generate_order.side_effect = lambda: {"order_id": "test-order"}
            send_orders_concurrently(num_orders)
        
        # Assert the publish_order method was called for each order
        self.assertEqual(mock_publisher.publish_order.call_count, num_orders)
        mock_publisher.publish_order.assert_called_with({"order_id": "test-order"})

    @patch('data_generator.publish_to_rabbitmq.RabbitMQOrderPublisher')
    def test_concurrent_threads_execution(self, MockRabbitMQOrderPublisher):
        """
        Test if ThreadPoolExecutor works for concurrent publishing.
        """
        # Mock the RabbitMQ publisher
        mock_publisher = MockRabbitMQOrderPublisher.return_value
        mock_publisher.publish_order = MagicMock()
        
        # Number of threads
        num_threads = 5
        
        # Generate mock orders
        orders = [{"order_id": f"test-order-{i}"} for i in range(num_threads)]
        
        # Concurrently publish orders using ThreadPoolExecutor
        def mock_send_order(order):
            publisher = RabbitMQOrderPublisher("localhost", "test_exchange", "test_key")
            publisher.publish_order(order)
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            executor.map(mock_send_order, orders)
        
        # Assert the publish_order method was called once per order
        self.assertEqual(mock_publisher.publish_order.call_count, num_threads)

    @patch('data_generator.publish_to_rabbitmq.RabbitMQOrderPublisher')
    def test_error_handling(self, MockRabbitMQOrderPublisher):
        """
        Test error handling when RabbitMQ connection fails.
        """
        # Mock the RabbitMQ publisher to raise an exception
        mock_publisher = MockRabbitMQOrderPublisher.return_value
        mock_publisher.publish_order.side_effect = Exception("Simulated connection error")
        
        # Number of orders to test
        num_orders = 5
        
        # Run the concurrent order sending
        with self.assertLogs('clothing_order_publisher', level='ERROR') as log:
            send_orders_concurrently(num_orders)
        
        # Assert logs contain the expected error messages
        for i in range(num_orders):
            self.assertIn("Simulated connection error", log.output[i])

# Run the tests
if __name__ == "__main__":
    unittest.main()
