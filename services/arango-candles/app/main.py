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
    """Подписка на команды управления (stop) из Kafka."""
    listener = KafkaControlListener(config.QUEUE_ID)
    await listener.start()
    async for command in listener.listen():
        if command.get("command") == "stop":
            logger.warning(f"🛑 Получена команда STOP: {command}")
            await telemetry.send_status_update(
                status="interrupted",
                message="Остановлено пользователем по команде",
                finished=True
            )
            stop_event.set()
            break
    await listener.stop()


async def main():
    telemetry = TelemetryProducer()
    await telemetry.start()
    logger.info(f"🚀 Старт arango-candles: {config.QUEUE_ID} -> {config.COLLECTION_NAME}")
    await telemetry.send_status_update(status="started", message="Arango-candles consumer started")

    consumer_task = asyncio.create_task(run_consumer(stop_event, telemetry))
    control_task = asyncio.create_task(handle_control_messages(telemetry))

    # Ждем завершения одной из задач
    done, pending = await asyncio.wait([consumer_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    # Отменяем оставшиеся задачи
    for task in pending:
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass # Ожидаемое исключение

    # Финальная телеметрия отправляется из consumer.py

    logger.info("✅ Завершение работы arango-candles.")
    await close_telemetry(telemetry)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Фатальная ошибка в arango-candles: {e}")