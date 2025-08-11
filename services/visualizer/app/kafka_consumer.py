from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from loguru import logger
import asyncio
import json

from app.settings import settings

class KafkaManager:
    def __init__(self):
        self.consumer = None
        self.producer = None

    async def start_consumer(self, topic: str, group_id: str = "visualizer-group"):
        logger.info(f"Starting Kafka consumer for topic: {topic}")
        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            auto_offset_reset="earliest",
            security_protocol="PLAINTEXT", # TODO: Add SSL/TLS support based on CA_PATH
        )
        await self.consumer.start()
        logger.info(f"Kafka consumer started for topic: {topic}")

    async def stop_consumer(self):
        if self.consumer:
            logger.info("Stopping Kafka consumer")
            await self.consumer.stop()
            logger.info("Kafka consumer stopped")

    async def consume_messages(self):
        if not self.consumer:
            logger.warning("Kafka consumer not started. Call start_consumer first.")
            return
        async for msg in self.consumer:
            logger.info(f"Consumed message from {msg.topic}: {msg.value.decode()}")
            yield json.loads(msg.value.decode())

    async def start_producer(self):
        logger.info("Starting Kafka producer")
        self.producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            security_protocol="PLAINTEXT", # TODO: Add SSL/TLS support based on CA_PATH
        )
        await self.producer.start()
        logger.info("Kafka producer started")

    async def stop_producer(self):
        if self.producer:
            logger.info("Stopping Kafka producer")
            await self.producer.stop()
            logger.info("Kafka producer stopped")

    async def send_message(self, topic: str, message: dict):
        if not self.producer:
            logger.warning("Kafka producer not started. Call start_producer first.")
            return
        await self.producer.send_and_wait(topic, json.dumps(message).encode())
        logger.info(f"Sent message to {topic}: {message}")

kafka_manager = KafkaManager()
