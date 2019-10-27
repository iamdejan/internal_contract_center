from django.apps import AppConfig

from contract.AMQPConsuming import AMQPConsuming

class ContractConfig(AppConfig):
    name = 'contract'
    def ready(self):
        consumer = AMQPConsuming()
        consumer.daemon = True
        consumer.start()
