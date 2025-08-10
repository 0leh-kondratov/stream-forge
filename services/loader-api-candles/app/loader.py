import asyncio
from loguru import logger
from datetime import datetime, timedelta
from app import config
from app.telemetry import TelemetryProducer
from app.kafka_producer import KafkaDataProducer
from app.api_client import BinanceAPIClient
from app.metrics import records_fetched_total, records_published_total, errors_total

async def run_loader(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    logger.info("Starting loader for API candles...")

    api_client = None
    data_producer = None
    try:
        api_client = BinanceAPIClient(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        data_producer = KafkaDataProducer()
        await data_producer.start()

        symbol = config.SYMBOL
        interval = config.INTERVAL
        time_range_str = config.TIME_RANGE

        # Parse time range
        start_date_str, end_date_str = time_range_str.split(':')
        start_time_ms = int(datetime.strptime(start_date_str, "%Y-%m-%d").timestamp() * 1000)
        end_time_ms = int(datetime.strptime(end_date_str, "%Y-%m-%d").timestamp() * 1000)

        current_time_ms = start_time_ms
        total_fetched = 0
        total_published = 0

        await telemetry.send_status_update(status="loading", message="Loader started, fetching historical data.")

        while current_time_ms < end_time_ms and not stop_event.is_set():
            klines = await api_client.get_klines(
                symbol=symbol,
                interval=interval,
                start_time=current_time_ms,
                limit=1000 # Max limit per request
            )

            if klines is None or not klines:
                logger.info(f"No more klines data for {symbol} from {datetime.fromtimestamp(current_time_ms / 1000)}.")
                break

            records_fetched_total.inc(len(klines))
            total_fetched += len(klines)

            for kline in klines:
                if stop_event.is_set():
                    logger.info("Stop event received, exiting loader loop.")
                    break
                
                # Process kline data (e.g., convert to dict, add metadata)
                candle_data = {
                    "open_time": kline[0],
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "close_time": kline[6],
                    "quote_asset_volume": float(kline[7]),
                    "number_of_trades": int(kline[8]),
                    "taker_buy_base_asset_volume": float(kline[9]),
                    "taker_buy_quote_asset_volume": float(kline[10]),
                    "symbol": symbol,
                    "interval": interval,
                }
                
                await data_producer.send(candle_data)
                records_published_total.inc()
                total_published += 1

            # Move to the next time window
            # Assuming klines are ordered by time, the last kline's close_time + 1ms is the next start_time
            if klines:
                current_time_ms = klines[-1][6] + 1 # Use close_time of last kline + 1ms
            else:
                # If no klines were fetched, advance by one interval to avoid infinite loop
                # This is a rough estimate, better to use actual interval duration
                if interval == '1m': time_advance = 60 * 1000
                elif interval == '1h': time_advance = 3600 * 1000
                elif interval == '1d': time_advance = 86400 * 1000
                else: time_advance = 3600 * 1000 # Default to 1 hour
                current_time_ms += time_advance

            await telemetry.send_status_update(
                status="loading",
                message=f"Fetched {total_fetched} and published {total_published} records.",
                records_written=total_published
            )
            await asyncio.sleep(0.1) # Small delay to avoid hitting API limits too fast

        logger.info(f"Loader finished. Total fetched: {total_fetched}, total published: {total_published}")
        await telemetry.send_status_update(
            status="finished",
            message=f"Loader finished. Total records published: {total_published}",
            finished=True,
            records_written=total_published
        )

    except asyncio.CancelledError:
        logger.info("Loader task cancelled.")
        await telemetry.send_status_update(status="interrupted", message="Loader task cancelled.")
    except Exception as e:
        logger.error(f"Fatal error in loader: {e}", exc_info=True)
        errors_total.inc()
        await telemetry.send_status_update(status="error", message="Fatal loader error", error_message=str(e))
    finally:
        if api_client:
            await api_client.close()
        if data_producer:
            await data_producer.stop()
        logger.info("Loader finished.")
