import ssl
from loguru import logger
from aiokafka import AIOKafkaConsumer
import asyncio
import json
from app import config

class KafkaControlListener:
    def __init__(self, queue_id: str):
        self.queue_id = queue_id
        self.consumer = None

    async def start(self):
        try:
            ssl_context = ssl.create_default_context(cafile=config.KAFKA_CA_PATH)
            self.consumer = AIOKafkaConsumer(
                config.QUEUE_CONTROL_TOPIC,
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=f"control-listener-{self.queue_id}",
                security_protocol="SASL_SSL",
                sasl_mechanism="SCRAM-SHA-512",
                sasl_plain_username=config.KAFKA_USER,
                sasl_plain_password=config.KAFKA_PASSWORD,
                ssl_context=ssl_context,
                auto_offset_reset="latest"
            )
            await self.consumer.start()
            logger.info(f"KafkaControlListener for {self.queue_id} connected to Kafka.")
        except Exception as e:
            logger.error(f"Failed to connect KafkaControlListener to Kafka: {e}")
            raise

    async def listen(self):
        try:
            async for msg in self.consumer:
                command = json.loads(msg.value.decode('utf-8'))
                logger.info(f"Received control command: {command}")
                # Filter commands by queue_id if necessary, or process all relevant commands
                if command.get("queue_id") == self.queue_id or command.get("queue_id") == "all":
                    yield command
        except asyncio.CancelledError:
            logger.info("KafkaControlListener task cancelled.")
        except Exception as e:
            logger.error(f"Error in KafkaControlListener: {e}")

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("KafkaControlListener disconnected from Kafka.")
