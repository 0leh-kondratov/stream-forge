# debug_producer.py
import argparse
import asyncio
import json
import os
import time
import ssl
from loguru import logger
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue-id", required=True)
    parser.add_argument("--command", required=True, choices=["ping", "stop"])
    parser.add_argument("--expect-pong", action="store_true")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--interval", type=float, default=1.0)
    return parser.parse_args()


def get_ssl_context():
    ca_path = os.getenv("KAFKA_CA_PATH")
    return ssl.create_default_context(cafile=ca_path)


async def send_command(producer, topic, payload):
    await producer.send_and_wait(topic, json.dumps(payload).encode())
    logger.info(f"Command sent: {payload['command']}")


async def wait_for_pong(queue_id, ping_ts, timeout=10.0):
    topic = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    username = os.getenv("KAFKA_USER")
    password: "REDACTED"("KAFKA_PASSWORD")

    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=username,
        sasl_plain_password=password,
        ssl_context=get_ssl_context(),
        group_id=f"debug-consumer-{queue_id}",
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()

    try:
        start = time.time()
        async for msg in consumer:
            payload = json.loads(msg.value.decode())
            if payload.get("event") == "pong" and payload.get("queue_id") == queue_id:
                pong_ts = payload.get("ponged_at")
                rtt = pong_ts - ping_ts
                logger.success(f"[pong] RTT: {rtt:.3f}s | sent: {ping_ts:.3f}, received: {pong_ts:.3f}")
                break
            if time.time() - start > timeout:
                logger.warning("Timeout waiting for pong")
                break
    finally:
        await consumer.stop()


async def main():
    args = parse_args()

    queue_id = args.queue_id
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
    username = os.getenv("KAFKA_USER")
    password: "REDACTED"("KAFKA_PASSWORD")
    control_topic = os.getenv("QUEUE_CONTROL_TOPIC", "queue-control")

    ssl_context = get_ssl_context()

    producer = AIOKafkaProducer(
        bootstrap_servers=bootstrap_servers,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=username,
        sasl_plain_password=password,
        ssl_context=ssl_context,
    )
    await producer.start()

    try:
        for i in range(args.repeat):
            ts = time.time()
            payload = {
                "queue_id": queue_id,
                "command": args.command,
                "sent_at": ts,
            }
            logger.info(f"[{i+1}/{args.repeat}] Sending {args.command} at {ts:.3f}")
            await send_command(producer, control_topic, payload)

            if args.command == "ping" and args.expect_pong:
                await wait_for_pong(queue_id, ts)

            if i < args.repeat - 1:
                await asyncio.sleep(args.interval)

    finally:
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
