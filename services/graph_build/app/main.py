import asyncio
from loguru import logger
import uvloop # Assuming uvloop is desired and installed
from fastapi import FastAPI
from app.metrics import metrics_router

from app import config
from app.kafka_control import KafkaControlListener
from app.builder import run_builder # Changed from consumer to builder
from app.telemetry import TelemetryProducer, close_telemetry

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()

# Initialize FastAPI app
app = FastAPI(title="Graph Build Service")
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
    logger.info(f"🚀 Starting Graph Build: {config.QUEUE_ID} -> {config.GRAPH_COLLECTION_NAME}")
    await telemetry.send_status_update(status="started", message="Graph Build consumer started")

    builder_task = asyncio.create_task(run_builder(stop_event, telemetry))
    control_task = asyncio.create_task(handle_control_messages(telemetry))

    # Wait for one of the tasks to complete
    done, pending = await asyncio.wait([builder_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel remaining tasks
    for task in pending:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass # Expected exception

    logger.info("✅ Graph Build shutdown complete.")
    await close_telemetry(telemetry)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Fatal error in Graph Build: {e}")
