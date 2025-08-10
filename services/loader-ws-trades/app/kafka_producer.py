import json
import ssl
from aiokafka import AIOKafkaProducer
from loguru import logger
from app import config

class KafkaDataProducer:
    def __init__(self):
        self.topic = config.KAFKA_TOPIC
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.username = config.KAFKA_USER_PRODUCER
        self.password = config.KAFKA_PASSWORD_PRODUCER
        self.ca_path = config.CA_PATH
        self.producer = None

    async def start(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(cafile=self.ca_path)
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
            ssl_context=ssl_context,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )
        await self.producer.start()
        logger.debug(f"Data producer started for topic: {self.topic}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("Data producer stopped.")

    async def send(self, data: dict):
        try:
            await self.producer.send_and_wait(self.topic, value=data)
            logger.debug(f"Data sent to Kafka topic {self.topic}")
        except Exception as e:
            logger.error(f"Error sending data to Kafka: {e}")
