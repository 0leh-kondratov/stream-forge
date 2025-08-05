import asyncio
from loguru import logger
import uvloop

from app.config import QUEUE_ID
from app.consumer import KafkaToArangoConsumer
from app.queue_state import is_queue_interrupted
from app.telemetry import send_event

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

stop_event = asyncio.Event()


async def run():
    logger.info(f"🚀 Старт arango-connector: {QUEUE_ID}")

    # Телеметрия: запуск consumer
    await send_event(status="started", message="Consumer started")

    consumer = KafkaToArangoConsumer()
    await consumer.start()

    try:
        await consumer.consume_and_store(stop_event)
    except Exception as e:
        logger.exception(f"❌ Ошибка в arango-connector: {e}")
        await send_event(status="error", message=str(e), finished=True)
    else:
        if not stop_event.is_set():
            logger.info("✅ Consumer завершил работу.")
            await send_event(status="finished", message="Consumer finished", finished=True)


def main():
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.warning("🛑 Прерывание пользователем.")
        stop_event.set()
    except Exception as e:
        logger.exception(f"❌ Ошибка выполнения: {e}")


if __name__ == "__main__":
    main()
