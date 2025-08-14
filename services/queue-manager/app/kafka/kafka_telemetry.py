import json
from aiokafka import AIOKafkaConsumer
from loguru import logger
from typing import AsyncGenerator

from app.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_USER,
    KAFKA_PASSWORD,
    CA_PATH,
    QUEUE_EVENTS_TOPIC,
)


class KafkaTelemetryReceiver:
    def __init__(self):
        self.consumer: AIOKafkaConsumer | None = None

    async def start(self, group_id: str = "queue-manager-telemetry"):
        self.consumer = AIOKafkaConsumer(
            QUEUE_EVENTS_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=KAFKA_USER,
            sasl_plain_password=KAFKA_PASSWORD,
            ssl_cafile=CA_PATH,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        logger.info("📥 KafkaTelemetryReceiver connected")

    async def listen(self) -> AsyncGenerator[dict, None]:
        if not self.consumer:
            raise RuntimeError("Telemetry consumer not initialized")
        async for msg in self.consumer:
            logger.debug(f"📨 Telemetry received: {msg.value}")
            yield msg.value

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("🛑 KafkaTelemetryReceiver stopped")
