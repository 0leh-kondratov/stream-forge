import asyncio
import argparse
import uvicorn
from contextlib import asynccontextmanager
from loguru import logger
import uvloop
from fastapi import FastAPI

from app import config
from app.metrics import metrics_router
from app.loader import run_loader
from app.kafka_client import KafkaControlListener
from app.telemetry import TelemetryProducer, close_telemetry

# Use uvloop for performance
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()

async def handle_control_messages(telemetry: TelemetryProducer):
    """
    Подписка на команды управления (stop) из Kafka.
    """
    listener = KafkaControlListener(config.QUEUE_ID)
    await listener.start()
    try:
        async for command in listener.listen():
            if command.get("command") == "stop":
                logger.warning(f"🛑 Получена команда STOP: {command}")
                await telemetry.send_status_update(
                    status="interrupted",
                    message="Остановлено пользователем",
                    finished=True
                )
                stop_event.set()
                break
    finally:
        await listener.stop()

async def run_app_logic():
    """The core logic of the application."""
    telemetry = TelemetryProducer()
    await telemetry.start()
    logger.info(f"🚀 Старт loader-producer: {config.QUEUE_ID} [{config.SYMBOL}, {config.TYPE}]")

    await telemetry.send_status_update(status="started", message="Loader started")

    loader_task = asyncio.create_task(run_loader(stop_event, telemetry))
    control_task = asyncio.create_task(handle_control_messages(telemetry))

    done, pending = await asyncio.wait([loader_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    for task in pending:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass

    logger.info("✅ Завершено успешно.")
    await close_telemetry(telemetry)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Lifespan startup")
    app_logic_task = asyncio.create_task(run_app_logic())
    yield
    # Shutdown
    logger.info("Lifespan shutdown")
    stop_event.set()
    await app_logic_task

# Initialize FastAPI app
app = FastAPI(title="Loader Producer Service", lifespan=lifespan)
app.include_router(metrics_router)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--noop", action="store_true", help="Accepted for compatibility, but does nothing.")
    args = parser.parse_args()

    if args.noop:
        logger.info("NOOP mode enabled, but starting server anyway for CI health check.")

    uvicorn.run(app, host="0.0.0.0", port=8080)
