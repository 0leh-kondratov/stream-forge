import json
from aiokafka import AIOKafkaConsumer
from loguru import logger
from app.config import (
    QUEUE_ID,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_USER,
    KAFKA_PASSWORD,
    CA_PATH,
    QUEUE_CONTROL_TOPIC,
)


class KafkaControlConsumer:
    """
    Kafka consumer для прослушивания команд управления (например: stop).
    """

    def __init__(self, queue_id: str):
        self.queue_id = queue_id
        self.consumer: AIOKafkaConsumer | None = None
        self.records_written: int = 0

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            QUEUE_CONTROL_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"{self.queue_id}-control-group",
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=KAFKA_USER,
            sasl_plain_password=KAFKA_PASSWORD,
            ssl_cafile=CA_PATH,
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        logger.info("📥 Kafka consumer запущен (управление очередью).")

    async def listen(self):
        if not self.consumer:
            raise RuntimeError("Consumer не инициализирован.")
        async for msg in self.consumer:
            command = msg.value
            if command.get("queue_id") == self.queue_id:
                yield command

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
            logger.info("🛑 Kafka consumer остановлен.")
