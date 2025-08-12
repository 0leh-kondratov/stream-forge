import asyncio
from loguru import logger
import uvloop
from fastapi import FastAPI # Import FastAPI
from app.metrics import metrics_router # Import metrics_router

from app import config
from app.kafka_control import KafkaControlListener
from app.consumer import run_consumer
from app.telemetry import TelemetryProducer, close_telemetry # Changed Telemetry to TelemetryProducer

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()

# Initialize FastAPI app
app = FastAPI(title="Arango Candles Service")
app.include_router(metrics_router)


async def handle_control_messages(telemetry: TelemetryProducer):
    """Subscribe to control commands (stop) from Kafka."""
    listener = KafkaControlListener(config.QUEUE_ID)
    await listener.start()
    async for command in listener.listen():
        if command.get("command") == "stop":
            logger.warning(f"🛑 STOP command received: {command}")
            await telemetry.send_status_update(
                status="interrupted",
                message="Stopped by user command",
                finished=True
            )
            stop_event.set()
            break
    await listener.stop()


async def main():
    telemetry = TelemetryProducer()
    await telemetry.start()
    logger.info(f"🚀 Starting arango-candles: {config.QUEUE_ID} -> {config.COLLECTION_NAME}")
    await telemetry.send_status_update(status="started", message="Arango-candles consumer started")

    consumer_task = asyncio.create_task(run_consumer(stop_event, telemetry))
    control_task = asyncio.create_task(handle_control_messages(telemetry))

    # Wait for one of the tasks to complete
    done, pending = await asyncio.wait([consumer_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel the remaining tasks
    for task in pending:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass # Expected exception

    # Final telemetry is sent from consumer.py

    logger.info("✅ Shutting down arango-candles.")
    await close_telemetry(telemetry)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Fatal error in arango-candles: {e}")