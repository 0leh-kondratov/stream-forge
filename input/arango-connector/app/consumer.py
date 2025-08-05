import asyncio
import json
from aiokafka import AIOKafkaConsumer
from loguru import logger

from app.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_USER,
    KAFKA_PASSWORD,
    CA_PATH,
    KAFKA_TOPIC,
    QUEUE_ID,
    SYMBOL,
    TYPE,
)
from app.arango_client import AsyncArangoConnector
from app.queue_state import is_queue_interrupted


class KafkaToArangoConsumer:
    def __init__(self):
        self.consumer: AIOKafkaConsumer | None = None
        self.arango = AsyncArangoConnector()
        self.collection_name = f"{SYMBOL}_{TYPE}".lower()

    async def start(self):
        await self.arango.connect()

        self.consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=f"{QUEUE_ID}-arango-group",
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=KAFKA_USER,
            sasl_plain_password=KAFKA_PASSWORD,
            ssl_cafile=CA_PATH,
            enable_auto_commit=True,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        logger.info("📥 Kafka consumer запущен (Arango connector).")

    async def consume_and_store(self, stop_event: asyncio.Event):
        try:
            assert self.consumer
            async for msg in self.consumer:
                if stop_event.is_set():
                    logger.warning("🛑 Consumer остановлен по событию.")
                    break

                if await is_queue_interrupted(self.arango.db, QUEUE_ID):
                    logger.warning("🚨 Очередь была остановлена пользователем.")
                    stop_event.set()
                    break

                try:
                    data = msg.value
                    if not isinstance(data, dict):
                        raise ValueError("Некорректный формат сообщения")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при разборе сообщения: {e}")
                    continue

                logger.debug(f"📩 Получено сообщение: {data}")
                await self.arango.insert_documents(collection_name=self.collection_name, docs=[data])

        except Exception as e:
            logger.exception(f"❌ Ошибка consumer'а: {e}")
        finally:
            await self.stop()

    async def stop(self):
        if self.consumer:
            await self.consumer.stop()
        await self.arango.close()
        logger.info("🛑 Consumer и Arango соединение закрыты.")
