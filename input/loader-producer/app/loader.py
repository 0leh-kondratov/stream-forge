import asyncio
from loguru import logger

from app.config import SYMBOL, TYPE, TELEMETRY_INTERVAL
from app.kafka_producer import KafkaMessageProducer
from app.telemetry import send_event
from app.utils import fetch_binance_data


async def run_loader(stop_event: asyncio.Event):
    """
    Главная логика загрузчика.
    """
    producer = KafkaMessageProducer()
    await producer.start()

    records_written = 0
    last_telemetry_sent = asyncio.get_event_loop().time()

    try:
        async for chunk in fetch_binance_data():
            if stop_event.is_set():
                logger.warning("🛑 Загрузка остановлена пользователем.")
                break

            for record in chunk:
                await producer.send(record)
            records_written += len(chunk)

            now = asyncio.get_event_loop().time()
            if now - last_telemetry_sent >= TELEMETRY_INTERVAL:
                await send_event(status="loading", records_written=records_written)
                last_telemetry_sent = now

    except Exception as e:
        logger.exception(f"❌ Ошибка загрузки: {e}")
        await send_event(
            status="error",
            message=str(e),
            records_written=records_written,
            finished=True
        )
    finally:
        await producer.stop()

        if not stop_event.is_set():
            await send_event(
                status="finished",
                message="✅ Загрузка завершена",
                records_written=records_written,
                finished=True
            )
        else:
            await send_event(
                status="interrupted",
                message="Остановлено пользователем",
                records_written=records_written,
                finished=True
            )
