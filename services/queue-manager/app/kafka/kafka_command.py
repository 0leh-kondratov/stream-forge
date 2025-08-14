import json
from aiokafka import AIOKafkaProducer
from loguru import logger

from app.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_USER,
    KAFKA_PASSWORD,
    CA_PATH,
    QUEUE_CONTROL_TOPIC,
)


class KafkaCommandSender:
    def __init__(self):
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=KAFKA_USER,
            sasl_plain_password=KAFKA_PASSWORD,
            ssl_cafile=CA_PATH,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )
        await self.producer.start()
        logger.info("📡 KafkaCommandSender initialized")

    async def send_command(self, command: dict):
        if not self.producer:
            raise RuntimeError("KafkaCommandSender not started")
        await self.producer.send_and_wait(QUEUE_CONTROL_TOPIC, value=command)
        logger.debug(f"📤 Command sent to Kafka: {command}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("🛑 KafkaCommandSender stopped")
