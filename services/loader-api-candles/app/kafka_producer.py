import ssl
from loguru import logger
from aiokafka import AIOKafkaProducer
import asyncio
import json
from app import config

class KafkaDataProducer:
    def __init__(self):
        self.producer = None

    async def start(self):
        try:
            ssl_context = ssl.create_default_context(cafile=config.CA_PATH)
            self.producer = AIOKafkaProducer(
                bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
                security_protocol="SASL_SSL",
                sasl_mechanism="SCRAM-SHA-512",
                sasl_plain_username=config.KAFKA_USER,
                sasl_plain_password=config.KAFKA_PASSWORD,
                ssl_context=ssl_context
            )
            await self.producer.start()
            logger.info("KafkaDataProducer connected to Kafka.")
        except Exception as e:
            logger.error(f"Failed to connect KafkaDataProducer to Kafka: {e}")
            raise

    async def send(self, data: dict):
        try:
            await self.producer.send_and_wait(config.KAFKA_TOPIC, json.dumps(data).encode('utf-8'))
            logger.debug(f"Sent data to Kafka topic {config.KAFKA_TOPIC}: {data}")
        except Exception as e:
            logger.error(f"Failed to send data to Kafka: {e}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("KafkaDataProducer disconnected from Kafka.")