import asyncio
from loguru import logger
import uvloop

from app import config
from app.loader import run_loader
from app.kafka_client import KafkaControlConsumer
from app.telemetry import send_event

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()


async def handle_control_messages():
    """
    Подписка на команды управления (stop) из Kafka.
    """
    consumer = KafkaControlConsumer(config.QUEUE_ID)
    await consumer.start()
    async for command in consumer.listen():
        if command.get("command") == "stop":
            logger.warning(f"🛑 Получена команда STOP: {command}")
            await send_event(
                status="interrupted",
                message="Остановлено пользователем",
                records_written=consumer.records_written,
                finished=True
            )
            stop_event.set()
            break


async def main():
    logger.info(f"🚀 Старт loader-producer: {config.QUEUE_ID} [{config.SYMBOL}, {config.TYPE}]")

    await send_event(status="started", message="Loader started")

    loader_task = asyncio.create_task(run_loader(stop_event))
    control_task = asyncio.create_task(handle_control_messages())

    await asyncio.wait([loader_task, control_task], return_when=asyncio.FIRST_COMPLETED)

    if not stop_event.is_set():
        await send_event(status="finished", message="Загрузка завершена", finished=True)
        logger.info("✅ Завершено успешно.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception(f"❌ Ошибка в процессе загрузки: {e}")
        asyncio.run(send_event(status="error", message=str(e), finished=True))
