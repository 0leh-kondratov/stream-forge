import asyncio
from loguru import logger
import uvloop
from fastapi import FastAPI # Import FastAPI
from app.metrics import metrics_router # Import metrics_router

from app import config
from app.loader import run_loader
from app.kafka_client import KafkaControlListener # Changed from KafkaControlConsumer
from app.telemetry import TelemetryProducer, close_telemetry # Changed from send_event

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()

# Initialize FastAPI app
app = FastAPI(title="Loader Producer Service")
app.include_router(metrics_router)


async def handle_control_messages(telemetry: TelemetryProducer): # Added telemetry parameter
    """
    Подписка на команды управления (stop) из Kafka.
    """
    listener = KafkaControlListener(config.QUEUE_ID) # Changed from KafkaControlConsumer
    await listener.start()
    try:
        async for command in listener.listen():
            if command.get("command") == "stop":
                logger.warning(f"🛑 Получена команда STOP: {command}")
                await telemetry.send_status_update( # Use telemetry instance
                    status="interrupted",
                    message="Остановлено пользователем",
                    # records_written=consumer.records_written, # records_written is not directly available here
                    finished=True
                )
                stop_event.set()
                break
    finally:
        await listener.stop()


async def main():
    telemetry = TelemetryProducer() # Instantiate TelemetryProducer
    await telemetry.start() # Start TelemetryProducer
    logger.info(f"🚀 Старт loader-producer: {config.QUEUE_ID} [{config.SYMBOL}, {config.TYPE}]")

    await telemetry.send_status_update(status="started", message="Loader started") # Use telemetry instance

    loader_task = asyncio.create_task(run_loader(stop_event, telemetry)) # Pass telemetry instance
    control_task = asyncio.create_task(handle_control_messages(telemetry)) # Pass telemetry instance

    done, pending = await asyncio.wait([loader_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    # Cancel remaining tasks
    for task in pending:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass # Expected exception

    logger.info("✅ Завершено успешно.")
    # Final telemetry status is sent from loader.py's finally block
    await close_telemetry(telemetry) # Close telemetry producer

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Ошибка в процессе загрузки: {e}")
        asyncio.run(TelemetryProducer().send_status_update(status="error", message=str(e), finished=True))