import ssl
from loguru import logger
from aiokafka import AIOKafkaProducer
import asyncio
import json
from app import config

class TelemetryProducer:
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
            logger.info("TelemetryProducer connected to Kafka.")
        except Exception as e:
            logger.error(f"Failed to connect TelemetryProducer to Kafka: {e}")
            raise

    async def send_status_update(self, status: str, message: str, finished: bool = False, records_written: int = 0, error_message: str = None):
        event = {
            "producer_id": config.TELEMETRY_PRODUCER_ID,
            "timestamp": asyncio.get_event_loop().time(),
            "status": status,
            "message": message,
            "finished": finished,
            "records_written": records_written,
        }
        if error_message:
            event["error_message"] = error_message

        try:
            await self.producer.send_and_wait(config.QUEUE_EVENTS_TOPIC, json.dumps(event).encode('utf-8'))
            logger.debug(f"Sent telemetry: {event}")
        except Exception as e:
            logger.error(f"Failed to send telemetry update: {e}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            logger.info("TelemetryProducer disconnected from Kafka.")

telemetry_producer_instance = None

async def close_telemetry(telemetry_producer: TelemetryProducer):
    await telemetry_producer.stop()
