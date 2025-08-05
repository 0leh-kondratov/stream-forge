import json
import time
from aiokafka import AIOKafkaProducer
from loguru import logger
from app import config

_telemetry_producer: AIOKafkaProducer | None = None


async def _get_producer() -> AIOKafkaProducer:
    global _telemetry_producer
    if _telemetry_producer is None:
        _telemetry_producer = AIOKafkaProducer(
            bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=config.KAFKA_USER,
            sasl_plain_password=config.KAFKA_PASSWORD,
            ssl_cafile=config.CA_PATH,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )
        await _telemetry_producer.start()
    return _telemetry_producer


class Telemetry:
    async def send(
        self,
        status: str,
        message: str | None = None,
        records_written: int | None = None,
        finished: bool = False,
    ):
        try:
            producer = await _get_producer()
            event = {
                "queue_id": config.QUEUE_ID, "symbol": config.SYMBOL, "type": config.TYPE,
                "status": status, "message": message, "records_written": records_written,
                "finished": finished, "producer": config.TELEMETRY_PRODUCER_ID, "timestamp": time.time(),
            }
            # Убираем None значения для чистоты
            event_clean = {k: v for k, v in event.items() if v is not None}
            await producer.send_and_wait(config.QUEUE_EVENTS_TOPIC, value=event_clean)
            logger.debug(f"📡 Телеметрия отправлена: {status}")
        except Exception as e:
            logger.error(f"⚠️ Ошибка отправки телеметрии: {e}")

async def close_telemetry():
    global _telemetry_producer
    if _telemetry_producer:
        await _telemetry_producer.stop()
        _telemetry_producer = None

