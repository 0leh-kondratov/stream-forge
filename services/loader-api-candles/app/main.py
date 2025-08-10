import asyncio
from loguru import logger
import uvloop # Assuming uvloop is desired and installed
from fastapi import FastAPI
from app.metrics import metrics_router

from app import config
from app.telemetry import TelemetryProducer, close_telemetry
from app.loader import run_loader # Import the loader function
from app.kafka_control import KafkaControlListener # Assuming we need a control listener

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()

# Initialize FastAPI app
app = FastAPI(title="Loader API Candles Service")
app.include_router(metrics_router)


async def handle_control_messages(telemetry: TelemetryProducer):
    """Subscribe to control (stop) commands from Kafka."""
    listener = KafkaControlListener(config.QUEUE_ID)
    await listener.start()
    try:
        async for command in listener.listen():
            if command.get("command") == "stop":
                logger.warning(f"🛑 Received STOP command: {command}")
                await telemetry.send_status_update(
                    status="interrupted",
                    message="Stopped by user command",
                    finished=True
                )
                stop_event.set()
                break
    finally:
        await listener.stop()


async def main():
    telemetry = TelemetryProducer()
    await telemetry.start()
    logger.info(f"🚀 Starting Loader API Candles: {config.QUEUE_ID} -> {config.KAFKA_TOPIC}")
    await telemetry.send_status_update(status="started", message="Loader API Candles started")

    loader_task = asyncio.create_task(run_loader(stop_event, telemetry))
    control_task = asyncio.create_task(handle_control_messages(telemetry))

    # Wait for one of the tasks to complete
    done, pending = await asyncio.wait([loader_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel remaining tasks
    for task in pending:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass # Expected exception

    logger.info("✅ Loader API Candles shutdown complete.")
    await close_telemetry(telemetry)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Fatal error in Loader API Candles: {e}")