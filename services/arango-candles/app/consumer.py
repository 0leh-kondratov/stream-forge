import asyncio
import json
import ssl
import pandas as pd
import pandas_ta as ta
from aiokafka import AIOKafkaConsumer
from arango import ArangoClient
from loguru import logger
from app import config
from app.telemetry import TelemetryProducer

async def calculate_and_update_indicators(collection, symbol: str, latest_timestamp: int):
    """
    Fetches recent candles, calculates technical indicators, and updates the latest candle document.
    """
    try:
        # 1. Fetch recent candles from ArangoDB to get enough data for calculations.
        aql_query = """
        FOR doc IN @@collection
            FILTER doc.symbol == @symbol AND doc.timestamp <= @latest_timestamp
            SORT doc.timestamp DESC
            LIMIT 300
            RETURN doc
        """
        cursor = collection.db.aql.execute(
            aql_query,
            bind_vars={
                "@collection": collection.name,
                "symbol": symbol,
                "latest_timestamp": latest_timestamp
            }
        )
        
        docs = [doc for doc in cursor][::-1]

        if not docs:
            logger.warning(f"No historical data found for symbol {symbol} to calculate indicators.")
            return

        # 2. Convert to Pandas DataFrame and prepare it
        df = pd.DataFrame(docs)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms') # Assuming timestamp is in milliseconds
        df = df.set_index('timestamp')
        
        df['open'] = df['open'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)

        # 3. Calculate indicators using pandas-ta
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.vwap(append=True)
        df.ta.atr(length=30, append=True) # ATR

        # 4. Get the latest calculated indicators
        latest_indicators = df.iloc[-1]
        update_data = {
            "EMA_50": latest_indicators.get('EMA_50'),
            "EMA_200": latest_indicators.get('EMA_200'),
            "RSI_14": latest_indicators.get('RSI_14'),
            "VWAP_D": latest_indicators.get('VWAP_D'),
            "ATR_30": latest_indicators.get('ATR_30')
        }
        
        update_data = {k: v for k, v in update_data.items() if v is not None and pd.notna(v)}

        if not update_data:
            logger.warning(f"Indicator calculation resulted in no data for {symbol} at {latest_timestamp}")
            return

        # 5. Update the latest candle document in ArangoDB
        latest_doc_key = docs[-1]['_key']
        collection.update(latest_doc_key, update_data)
        logger.debug(f"Updated indicators for {symbol} at {latest_timestamp}: {update_data}")

    except Exception as e:
        logger.error(f"Failed to calculate or update indicators for {symbol}: {e}", exc_info=True)


async def run_consumer(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    logger.info("Starting Kafka consumer for candle data...")

    # Kafka Consumer Setup
    ssl_context = ssl.create_default_context(cafile=config.CA_PATH)
    consumer = AIOKafkaConsumer(
        config.KAFKA_TOPIC,
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=config.KAFKA_USER,
        sasl_plain_password=config.KAFKA_PASSWORD,
        ssl_context=ssl_context,
        group_id=f"arango-candles-consumer-{config.QUEUE_ID}",
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )
    await consumer.start()
    logger.info(f"Kafka consumer connected to topic: {config.KAFKA_TOPIC}")

    # ArangoDB Client Setup
    client = ArangoClient(hosts=config.ARANGO_URL)
    db = client.db(
        config.ARANGO_DB,
        username=config.ARANGO_USER,
        password=config.ARANGO_PASSWORD,
    )
    collection = db.collection(config.COLLECTION_NAME)
    logger.info(f"Connected to ArangoDB collection: {config.COLLECTION_NAME}")

    records_processed = 0
    try:
        await telemetry.send_status_update(status="loading", message="Consumer started, processing data.")
        async for msg in consumer:
            if stop_event.is_set():
                logger.info("Stop event received, exiting consumer loop.")
                break

            try:
                candle_data = json.loads(msg.value.decode("utf-8"))
                
                if "_key" not in candle_data and "timestamp" in candle_data and "symbol" in candle_data:
                    candle_data["_key"] = f"{candle_data['symbol']}-{candle_data['timestamp']}"
                
                collection.insert(candle_data, overwrite=True)
                records_processed += 1
                logger.debug(f"Inserted record: {candle_data.get('_key', 'N/A')}")

                await calculate_and_update_indicators(
                    collection,
                    candle_data['symbol'],
                    candle_data['timestamp']
                )

                if records_processed % 100 == 0:
                    await telemetry.send_status_update(
                        status="loading",
                        message=f"Processed {records_processed} records.",
                        records_written=records_processed
                    )

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from Kafka message: {msg.value}")
                await telemetry.send_status_update(status="error", message="JSON decode error", error_message=f"Failed to decode JSON: {msg.value}")
            except Exception as e:
                logger.error(f"Error processing candle data: {e}", exc_info=True)
                await telemetry.send_status_update(status="error", message="Data processing error", error_message=str(e))

    except asyncio.CancelledError:
        logger.info("Consumer task cancelled.")
        await telemetry.send_status_update(status="interrupted", message="Consumer task cancelled.")
    except Exception as e:
        logger.error(f"Fatal error in consumer: {e}", exc_info=True)
        await telemetry.send_status_update(status="error", message="Fatal consumer error", error_message=str(e))
    finally:
        await consumer.stop()
        logger.info(f"Kafka consumer stopped. Total records processed: {records_processed}")
        await telemetry.send_status_update(
            status="finished",
            message=f"Consumer finished. Total records written: {records_processed}",
            finished=True,
            records_written=records_processed
        )