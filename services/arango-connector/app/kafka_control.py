import asyncio
import json
import ssl
from aiokafka import AIOKafkaConsumer
from loguru import logger
from app import config

class KafkaControlListener:
    def __init__(self, queue_id: str):
        self.queue_id = queue_id
        self.topic = config.QUEUE_CONTROL_TOPIC
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.username = config.KAFKA_USER
        self.password = config.KAFKA_PASSWORD
        self.ca_path = config.CA_PATH
        self.consumer = None

    async def start(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(cafile=self.ca_path)

        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
            ssl_context=ssl_context,
            group_id=f"control-listener-{self.queue_id}", # Unique group ID
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await self.consumer.start()
        logger.info(f"Kafka control listener started for queue_id: {self.queue_id}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("Kafka control listener stopped.")

    async def listen(self):
        """Asynchronously yields control commands relevant to this queue_id."""
        async for msg in self.consumer:
            try:
                command = json.loads(msg.value.decode("utf-8"))
                if command.get("queue_id") == self.queue_id:
                    logger.debug(f"Received control command for {self.queue_id}: {command}")
                    yield command
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from Kafka message: {msg.value}")
            except Exception as e:
                logger.error(f"Error processing Kafka control message: {e}")
