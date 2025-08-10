import asyncio
from loguru import logger
from datetime import datetime, timedelta
from app import config
from app.telemetry import TelemetryProducer
from app.kafka_producer import KafkaDataProducer
from app.api_client import BinanceAPIClient
from app.metrics import records_fetched_total, records_published_total, errors_total

async def run_loader(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    logger.info("Starting loader for API trades...")

    api_client = None
    data_producer = None
    try:
        api_client = BinanceAPIClient(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)
        data_producer = KafkaDataProducer()
        await data_producer.start()

        symbol = config.SYMBOL
        limit = config.LIMIT
        time_range_str = config.TIME_RANGE

        # Parse time range
        start_date_str, end_date_str = time_range_str.split(':')
        start_time_ms = int(datetime.strptime(start_date_str, "%Y-%m-%d").timestamp() * 1000)
        end_time_ms = int(datetime.strptime(end_date_str, "%Y-%m-%d").timestamp() * 1000)

        current_time_ms = start_time_ms
        total_fetched = 0
        total_published = 0

        await telemetry.send_status_update(status="loading", message="Loader started, fetching historical trade data.")

        while current_time_ms < end_time_ms and not stop_event.is_set():
            trades = await api_client.get_historical_trades(
                symbol=symbol,
                start_time=current_time_ms,
                limit=limit # Max limit per request
            )

            if trades is None or not trades:
                logger.info(f"No more trades data for {symbol} from {datetime.fromtimestamp(current_time_ms / 1000)}.")
                break

            records_fetched_total.inc(len(trades))
            total_fetched += len(trades)

            for trade in trades:
                if stop_event.is_set():
                    logger.info("Stop event received, exiting loader loop.")
                    break
                
                # Process trade data (e.g., convert to dict, add metadata)
                trade_data = {
                    "trade_id": trade['a'], # Aggregate tradeId
                    "price": float(trade['p']),
                    "quantity": float(trade['q']),
                    "first_trade_id": trade['f'],
                    "last_trade_id": trade['l'],
                    "timestamp": trade['T'], # Trade time
                    "is_buyer_maker": trade['m'],
                    "is_best_match": trade['M'],
                    "symbol": symbol,
                }
                
                await data_producer.send(trade_data)
                records_published_total.inc()
                total_published += 1

            # Move to the next time window
            # Assuming trades are ordered by time, the last trade's timestamp + 1ms is the next start_time
            if trades:
                current_time_ms = trades[-1]['T'] + 1 # Use timestamp of last trade + 1ms
            else:
                # If no trades were fetched, advance by one day to avoid infinite loop
                current_time_ms += 86400 * 1000 # Advance by 1 day in milliseconds

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
