import asyncio
from loguru import logger
import orjson # For faster JSON processing
from app import config
from app.telemetry import TelemetryProducer
from app.kafka_producer import KafkaDataProducer
from app.ws_client import BinanceWSClient
from app.metrics import records_fetched_total, records_published_total, errors_total

async def run_loader(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    logger.info("Starting loader for WebSocket trades...")

    ws_client = None
    data_producer = None
    try:
        # Determine stream type based on config.TYPE (e.g., "ws_trade")
        stream_type = config.TYPE.replace("ws_", "") # Remove "ws_" prefix

        ws_client = BinanceWSClient(
            symbol=config.SYMBOL,
            stream_type=stream_type
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

            # Binance trade WebSocket messages have a specific structure
            # Example: {"e":"trade","E":1678886400000,"s":"BTCUSDT","t":12345,"p":"20000.00","q":"1.0","b":100,"a":101,"T":1678886400000,"m":true,"M":true}
            if message and message.get("e") == "trade":
                trade_data_ws = message
                
                # Process trade data (e.g., convert to dict, add metadata)
                trade_data = {
                    "trade_id": trade_data_ws["t"],
                    "price": float(trade_data_ws["p"]),
                    "quantity": float(trade_data_ws["q"]),
                    "timestamp": trade_data_ws["T"],
                    "is_buyer_maker": trade_data_ws["m"],
                    "symbol": trade_data_ws["s"],
                }
                
                await data_producer.send(trade_data)
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
                logger.debug(f"Processed WS trade for {trade_data['symbol']}.")

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
