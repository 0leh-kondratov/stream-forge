# app/kafka_consumer.py
import os
import json
import time
import ssl
import asyncio
from loguru import logger
from aiokafka import AIOKafkaConsumer
from app.metrics import dummy_pings_total, dummy_pongs_total

class KafkaCommandConsumer:
    def __init__(self, queue_id, telemetry_producer, exit_on_ping=False, shutdown_event: asyncio.Event = None):
        self.topic = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
        self.username = os.getenv("KAFKA_USER")
        self.password = os.getenv("KAFKA_PASSWORD")
        self.ca_path = os.getenv("KAFKA_CA_PATH")
        self.group_id = f"consumer-{queue_id}"
        self.queue_id = queue_id
        self.telemetry = telemetry_producer
        self.exit_on_ping = exit_on_ping
        self.shutdown_event = shutdown_event or asyncio.Event()
        self.consumer = None
        self._task = None

    async def start(self):
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.load_verify_locations(cafile=self.ca_path)
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            security_protocol="SASL_SSL",
            sasl_mechanism="SCRAM-SHA-512",
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
            ssl_context=ssl_context,
            group_id=self.group_id,
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        await self.consumer.start()
        logger.debug("Kafka consumer started")
        self._task = asyncio.create_task(self.consume())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self.consumer:
            await self.consumer.stop()
        logger.debug("Kafka consumer stopped")

    async def consume(self):
        logger.info(f"Kafka consumer initialized with queue_id: {self.queue_id}")
        try:
            async for msg in self.consumer:
                try:
                    payload = json.loads(msg.value.decode())
                    command = payload.get("command")
                    target_id = payload.get("queue_id")
                    logger.debug(f"Received command: {payload}")
                    logger.info(f"Payload type: {type(payload)}, target_id type: {type(target_id)}, self.queue_id type: {type(self.queue_id)}")

                    logger.info(f"Comparing target_id: '{target_id}' with self.queue_id: '{self.queue_id}'. Match: {target_id == self.queue_id}")

                    if target_id != self.queue_id:
                        continue

                    if command == "ping":
                        logger.info(f"Processing PING command for queue_id: {self.queue_id}")
                        dummy_pings_total.inc()
                        pong_payload = {
                            "ping_ts": payload.get("sent_at"),
                            "ponged_at": time.time(),
                            "queue_id": self.queue_id,
                        }
                        logger.info(f"Attempting to send pong with payload: {pong_payload}")
                        logger.info("About to send pong event.")
                        await self.telemetry.send_event("pong", pong_payload)
                        dummy_pongs_total.inc()
                        logger.info("Processed ping → sent pong")
                        if self.exit_on_ping:
                            logger.info("Exiting on --exit-on-ping")
                            self.shutdown_event.set()
                            return

                    elif command == "stop":
                        logger.info("Received stop command")
                        await self.telemetry.send_status_update(
                            status="interrupted",
                            message="Получена команда остановки",
                            finished=True,
                        )
                        self.shutdown_event.set()
                        return

                except Exception as e:
                    logger.error(f"Failed to process message: {e}")

        except asyncio.CancelledError:
            logger.warning("Kafka consumer task cancelled")
        except Exception as e:
            logger.error(f"Kafka consume loop failed: {e}")
