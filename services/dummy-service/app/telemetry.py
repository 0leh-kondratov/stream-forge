import asyncio

# app/telemetry.py
import os
import json
import time
import ssl
from loguru import logger
from aiokafka import AIOKafkaProducer
from app.metrics import dummy_events_total, dummy_status_last, dummy_errors_total


class TelemetryProducer:
    def __init__(self):
        self.topic = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.username = os.getenv("KAFKA_USER")
        self.password = os.getenv("KAFKA_PASSWORD")
        self.ca_path = os.getenv("KAFKA_CA_PATH")
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
        )
        await self.producer.start()
        logger.debug("Telemetry producer started.")

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_event(self, event_type: str, extra: dict = None):
        payload = {
            "event": event_type,
            "queue_id": os.getenv("QUEUE_ID"),
            "symbol": os.getenv("SYMBOL"),
            "type": os.getenv("TYPE", "dummy"),
            "producer": os.getenv("TELEMETRY_PRODUCER_ID", "dummy"),
            "sent_at": time.time(),
        }
        if extra:
            payload.update(extra)

        dummy_events_total.labels(event_type).inc()
        print(f"DEBUG: dummy_events_total.labels called with {event_type}")
        if event_type in {"started", "loading", "finished", "interrupted", "error"}:
            dummy_status_last.labels(event_type).set(1)
            print(f"DEBUG: dummy_status_last.labels called with {event_type}")

        await self.producer.send_and_wait(self.topic, json.dumps(payload).encode())
        logger.info(f"Event sent: {event_type}")

    async def send_status_update(self, status: str, message: str = None,
                                 finished: bool = False, records_written: int = 0,
                                 error_message: str = None, extra: dict = None):
        payload = {
            "status": status,
            "message": message or "",
            "finished": finished,
            "records_written": records_written,
            "time_range": os.getenv("TIME_RANGE"),
            "kafka": self.bootstrap_servers,
            "kafka_user": self.username,
            "kafka_topic": os.getenv("KAFKA_TOPIC"),
            "k8s_namespace": os.getenv("K8S_NAMESPACE"),
            "arango_url": os.getenv("ARANGO_URL"),
            "arango_db": os.getenv("ARANGO_DB"),
            "loader_image": os.getenv("LOADER_IMAGE"),
            "consumer_image": os.getenv("CONSUMER_IMAGE"),
        }
        if error_message:
            payload["error_message"] = error_message
        if extra:
            payload.update(extra)

        logger.info(f"Telemetry status update:\n{json.dumps(payload, indent=2)}")
        await self.send_event(status, payload)


async def log_startup_event(telemetry: TelemetryProducer):
    await telemetry.send_status_update(
        status="started",
        message="Микросервис запущен",
        finished=False,
        records_written=0,
    )


async def simulate_loading(telemetry: TelemetryProducer):
    count = 0
    while True:
        await asyncio.sleep(10)
        count += 1
        await telemetry.send_status_update(
            status="loading",
            message=f"Загрузка продолжается, batch {count}",
            records_written=count * 100
        )


async def simulate_failure(delay_sec: int, telemetry: TelemetryProducer):
    await asyncio.sleep(delay_sec)
    await telemetry.send_status_update(
        status="error",
        message="Ошибка тестовая: симулирован сбой",
        finished=True,
        error_message="Simulated failure triggered by --fail-after"
    )
    logger.error("Simulated failure — exiting")
    import sys
    sys.exit(1)
