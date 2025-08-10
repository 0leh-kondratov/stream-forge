import asyncio
from loguru import logger
import orjson # For faster JSON processing
from app import config
from app.telemetry import TelemetryProducer
from app.kafka_producer import KafkaDataProducer
from app.ws_client import BinanceWSClient
from app.metrics import records_fetched_total, records_published_total, errors_total

async def run_loader(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    logger.info("Starting loader for WebSocket candles...")

    ws_client = None
    data_producer = None
    try:
        ws_client = BinanceWSClient(
            symbol=config.SYMBOL,
            stream_type="kline", # Always kline for candles
            interval=config.INTERVAL
        )
        data_producer = KafkaDataProducer()
        await data_producer.start()

        total_fetched = 0
        total_published = 0

        await telemetry.send_status_update(status="loading", message="Loader started, connecting to WebSocket.")

        async for message in ws_client.connect():
            if stop_event.is_set():
                logger.info("Stop event received, exiting loader loop.")
                break

            # Binance kline WebSocket messages have a specific structure
            # Example: {"e":"kline","E":1678886400000,"s":"BTCUSDT","k":{"t":1678886400000,...}}
            if message and message.get("e") == "kline":
                kline_data = message["k"]
                
                # Process kline data (e.g., convert to dict, add metadata)
                candle_data = {
                    "open_time": kline_data["t"],
                    "open": float(kline_data["o"]),
                    "high": float(kline_data["h"]),
                    "low": float(kline_data["l"]),
                    "close": float(kline_data["c"]),
                    "volume": float(kline_data["v"]),
                    "close_time": kline_data["T"],
                    "quote_asset_volume": float(kline_data["q"]),
                    "number_of_trades": int(kline_data["n"]),
                    "taker_buy_base_asset_volume": float(kline_data["V"]),
                    "taker_buy_quote_asset_volume": float(kline_data["Q"]),
                    "symbol": kline_data["s"],
                    "interval": config.INTERVAL,
                }
                
                await data_producer.send(candle_data)
                records_fetched_total.inc()
                records_published_total.inc()
                total_fetched += 1
                total_published += 1

                if total_published % 100 == 0: # Send telemetry update every 100 records
                    await telemetry.send_status_update(
                        status="loading",
                        message=f"Fetched {total_fetched} and published {total_published} records.",
                        records_written=total_published
                    )
                logger.debug(f"Processed WS kline for {candle_data['symbol']}-{candle_data['interval']}.")

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
        if data_producer:
            await data_producer.stop()
        logger.info("Loader finished.")
