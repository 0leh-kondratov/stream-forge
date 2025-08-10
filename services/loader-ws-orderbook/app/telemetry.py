import json
import time
import ssl
from aiokafka import AIOKafkaProducer
from loguru import logger
from app import config
from app.metrics import events_total, status_last, errors_total # Import new metrics

class TelemetryProducer:
    def __init__(self):
        self.topic = config.TELEMETRY_TOPIC # Use TELEMETRY_TOPIC from config
        self.bootstrap_servers = config.KAFKA_BOOTSTRAP_SERVERS
        self.username = config.KAFKA_USER_PRODUCER # Use KAFKA_USER_PRODUCER
        self.password = config.KAFKA_PASSWORD_PRODUCER # Use KAFKA_PASSWORD_PRODUCER
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
            value_serializer=lambda m: json.dumps(m).encode("utf-8"), # Keep serializer
        )
        await self.producer.start()
        logger.debug("Telemetry producer started.")

    async def stop(self):
        if self.producer:
            await self.producer.stop()
            self.producer = None # Clear producer after stopping

    async def send_event(self, event_type: str, extra: dict = None):
        payload = {
            "event": event_type,
            "queue_id": config.QUEUE_ID,
            "symbol": config.SYMBOL,
            "type": config.TYPE,
            "producer": config.TELEMETRY_PRODUCER_ID,
            "sent_at": time.time(),
        }
        if extra:
            payload.update(extra)

        # Prometheus metrics integration
        events_total.labels(event_type).inc()
        if event_type in {"started", "loading", "finished", "interrupted", "error"}:
            status_last.labels(event_type).set(1)
        if event_type == "error": # Assuming "error" event means an error occurred
            errors_total.inc()

        try:
            await self.producer.send_and_wait(self.topic, value=payload)
            logger.info(f"Event sent: {event_type}")
        except Exception as e:
            logger.error(f"⚠️ Error sending telemetry: {e}")
            errors_total.inc() # Increment error metric on send failure

    async def send_status_update(self, status: str, message: str = None,
                                 finished: bool = False, records_written: int = 0,
                                 error_message: str = None, extra: dict = None):
        payload = {
            "status": status,
            "message": message or "",
            "finished": finished,
            "records_written": records_written,
            # Add other relevant config values from arango-candles config.py
            "kafka": self.bootstrap_servers,
            "kafka_user": self.username,
            "kafka_topic": config.KAFKA_TOPIC,
            # Remove ArangoDB specific fields as they are not relevant for loader-producer
        }
        if error_message:
            payload["error_message"] = error_message
        if extra:
            payload.update(extra)

        logger.info(f"Telemetry status update:\n{json.dumps(payload, indent=2)}")
        await self.send_event(status, payload)

# Update close_telemetry to use the new class structure
async def close_telemetry(telemetry_producer: TelemetryProducer):
    await telemetry_producer.stop()
