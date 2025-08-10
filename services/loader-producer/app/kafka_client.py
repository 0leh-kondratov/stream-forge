import asyncio
import json
import ssl # Import ssl for SSLContext
from aiokafka import AIOKafkaConsumer
from loguru import logger
from app import config # Import config

class KafkaControlListener: # Renamed from KafkaControlConsumer
    """
    Kafka consumer for listening to control commands (e.g., stop).
    """
    def __init__(self, queue_id: str):
        self.queue_id = queue_id
        self.topic = config.QUEUE_CONTROL_TOPIC # Use config
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS # Use config
        self.username = config.KAFKA_USER_CONSUMER # Use KAFKA_USER_CONSUMER
        self.password = config.KAFKA_PASSWORD_CONSUMER # Use KAFKA_PASSWORD_CONSUMER
        self.ca_path = config.CA_PATH # Use config
        self.consumer = None

    async def start(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) # Use ssl.SSLContext
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(cafile=self.ca_path)

        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=f"control-listener-{self.queue_id}", # Consistent group ID
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
            ssl_context=ssl_context, # Use ssl_context
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        logger.info(f"Kafka control listener started for queue_id: {self.queue_id}") # Consistent log message

    async def listen(self):
        if not self.consumer:
            raise RuntimeError("Consumer not initialized.")
        async for msg in self.consumer:
            command = msg.value
            if command.get("queue_id") == self.queue_id:
                yield command

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka control listener stopped.") # Consistent log message