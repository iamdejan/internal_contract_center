from django.apps import AppConfig

class ContractConfig(AppConfig):
    name = 'contract'
    def ready(self):
        from contract.AMQPConsuming import AMQPConsuming
        consumer = AMQPConsuming()
        consumer.daemon = True
        consumer.start()
