import json
from aiokafka import AIOKafkaProducer
from loguru import logger

from app.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
    KAFKA_USER,
    KAFKA_PASSWORD,
    CA_PATH,
)


class KafkaMessageProducer:
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
        logger.info("✅ Kafka producer инициализирован.")

    async def send(self, data: dict):
        if not self.producer:
            raise RuntimeError("Kafka producer не инициализирован")

        try:
            await self.producer.send_and_wait(KAFKA_TOPIC, value=data)
        except Exception as e:
            logger.exception(f"❌ Ошибка при отправке сообщения в Kafka: {e}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("🛑 Kafka producer остановлен.")
