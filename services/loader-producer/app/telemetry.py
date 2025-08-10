import json
import time
from aiokafka import AIOKafkaProducer
from loguru import logger
from app.config import (
    QUEUE_EVENTS_TOPIC,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_USER,
    KAFKA_PASSWORD,
    CA_PATH,
    QUEUE_ID,
    SYMBOL,
    TYPE,
    TELEMETRY_PRODUCER_ID,
)

_telemetry_producer: AIOKafkaProducer | None = None


async def _get_telemetry_producer() -> AIOKafkaProducer:
    global _telemetry_producer
    if _telemetry_producer is None:
        _telemetry_producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=KAFKA_USER,
            sasl_plain_password=KAFKA_PASSWORD,
            ssl_cafile=CA_PATH,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )
        await _telemetry_producer.start()
        logger.info("📡 Kafka telemetry producer подключен.")
    return _telemetry_producer


async def send_event(
    status: str,
    message: str | None = None,
    records_written: int | None = None,
    finished: bool = False,
):
    try:
        producer = await _get_telemetry_producer()
        event = {
            "queue_id": QUEUE_ID,
            "symbol": SYMBOL,
            "type": TYPE,
            "status": status,
            "message": message,
            "records_written": records_written,
            "finished": finished,
            "producer": TELEMETRY_PRODUCER_ID,
            "timestamp": time.time(),
        }
        await producer.send_and_wait(QUEUE_EVENTS_TOPIC, value=event)
        logger.debug(f"📡 Телеметрия отправлена: {status}")
    except Exception as e:
        logger.error(f"⚠️ Ошибка отправки телеметрии: {e}")


async def close_telemetry():
    global _telemetry_producer
    if _telemetry_producer:
        await _telemetry_producer.stop()
        logger.info("🛑 Kafka telemetry producer остановлен.")
        _telemetry_producer = None

