# main.py
import argparse
import asyncio
import os
import signal
from fastapi import FastAPI
from loguru import logger
from app.kafka_consumer import KafkaCommandConsumer
from app.telemetry import (
    TelemetryProducer,
    log_startup_event,
    simulate_loading,
    simulate_failure,
)
from app.metrics import metrics_router

app = FastAPI(title="Dummy Service")
app.include_router(metrics_router)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Включить отладочный режим")
    parser.add_argument("--noop", action="store_true", help="Не запускать Kafka consumer")
    parser.add_argument("--exit-on-ping", action="store_true", help="Завершить при первом ping")
    parser.add_argument("--exit-after", type=int, help="Завершить через N секунд")
    parser.add_argument("--simulate-loading", action="store_true", help="Имитировать статус loading")
    parser.add_argument("--fail-after", type=int, help="Завершить ошибкой через N секунд")
    return parser.parse_args()

def configure_logging(debug: bool):
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="{time:iso}|{level}|{message}",
        serialize=True,
        level="DEBUG" if debug else "INFO",
    )

def setup_signal_handlers(shutdown_event: asyncio.Event):
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

async def main():
    args = parse_args()
    configure_logging(args.debug)
    shutdown_event = asyncio.Event()
    setup_signal_handlers(shutdown_event)

    telemetry = TelemetryProducer()
    await telemetry.start()
    await log_startup_event(telemetry)

    if args.simulate_loading:
        asyncio.create_task(simulate_loading(telemetry))

    if args.fail_after:
        asyncio.create_task(simulate_failure(args.fail_after, telemetry))

    if args.noop:
        logger.info("Noop mode enabled — skipping Kafka consumer")
        await shutdown_event.wait()
    else:
        consumer = KafkaCommandConsumer(
            queue_id=os.getenv("QUEUE_ID"),
            telemetry_producer=telemetry,
            exit_on_ping=args.exit_on_ping,
            shutdown_event=shutdown_event,
        )
        await consumer.start()

        if args.exit_after:
            await asyncio.sleep(args.exit_after)
            logger.info(f"Exiting after {args.exit_after} seconds")
            shutdown_event.set()

        await shutdown_event.wait()
        await consumer.stop()

    await telemetry.send_status_update(
        status="finished",
        message="Микросервис завершил работу",
        finished=True,
        records_written=999
    )
    await telemetry.stop()

if __name__ == "__main__":
    asyncio.run(main())
