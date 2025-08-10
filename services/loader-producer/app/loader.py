import asyncio
from loguru import logger

from app.config import SYMBOL, TYPE, TELEMETRY_INTERVAL
from app.kafka_producer import KafkaDataProducer # Changed from KafkaMessageProducer
from app.telemetry import TelemetryProducer # Import TelemetryProducer
from app.utils import fetch_binance_data


async def run_loader(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    """
    Главная логика загрузчика.
    """
    producer = KafkaDataProducer() # Changed from KafkaMessageProducer
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
                await telemetry.send_status_update(status="loading", records_written=records_written) # Use telemetry instance
                last_telemetry_sent = now

    except Exception as e:
        logger.exception(f"❌ Ошибка загрузки: {e}")
        await telemetry.send_status_update( # Use telemetry instance
            status="error",
            message=str(e),
            records_written=records_written,
            finished=True
        )
    finally:
        await producer.stop()

        if not stop_event.is_set():
            await telemetry.send_status_update( # Use telemetry instance
                status="finished",
                message="✅ Загрузка завершена",
                records_written=records_written,
                finished=True
            )
        else:
            await telemetry.send_status_update( # Use telemetry instance
                status="interrupted",
                message="Остановлено пользователем",
                records_written=records_written,
                finished=True
            )