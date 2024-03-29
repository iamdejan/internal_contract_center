import threading

import pika

from . import constants
from .callbacks.contract import callback

class AMQPConsuming(threading.Thread):
    @staticmethod
    def _get_connection():
        parameters = pika.URLParameters("amqp://localhost")
        return pika.BlockingConnection(parameters)

    def run(self):
        # start
        connection = self._get_connection()
        channel = connection.channel()

        channel.queue_declare(queue = constants.VALIDATE_CHAIN)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            queue = constants.VALIDATE_CHAIN,
            auto_ack = True,
            on_message_callback = callback
        )
        channel.start_consuming()
        pass