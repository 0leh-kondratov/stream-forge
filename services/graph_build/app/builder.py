import asyncio
import json
import ssl
from aiokafka import AIOKafkaConsumer
from arango import ArangoClient
from loguru import logger
from app import config
from app.telemetry import TelemetryProducer

async def run_builder(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    logger.info("Starting Kafka consumer for graph building data...")

    # Kafka Consumer Setup
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(cafile=config.CA_PATH)

    consumer = AIOKafkaConsumer(
        config.KAFKA_TOPIC,
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-512",
        sasl_plain_username=config.KAFKA_USER,
        sasl_plain_password=config.KAFKA_PASSWORD,
        ssl_context=ssl_context,
        group_id=f"graph-build-consumer-{config.QUEUE_ID}", # Unique group ID
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
    # Assuming we'll store graph data in a collection named by GRAPH_COLLECTION_NAME
    graph_collection = db.collection(config.GRAPH_COLLECTION_NAME)
    logger.info(f"Connected to ArangoDB graph collection: {config.GRAPH_COLLECTION_NAME}")

    records_processed = 0
    try:
        await telemetry.send_status_update(status="loading", message="Consumer started, processing data for graph building.")
        async for msg in consumer:
            if stop_event.is_set():
                logger.info("Stop event received, exiting builder loop.")
                break

            try:
                prepared_data = json.loads(msg.value.decode("utf-8"))
                
                # --- Graph Building Logic ---
                # This is a placeholder. Actual graph building logic would go here.
                # It would involve:
                # 1. Extracting nodes and edges from prepared_data.
                # 2. Creating/updating documents in ArangoDB for nodes and edges.
                #    ArangoDB supports graph collections directly.
                # For demonstration, let's just insert the prepared data as a document
                # and assume it represents a graph snapshot or a part of it.
                
                # Example: If prepared_data contains '_key', use it for UPSERT
                # Otherwise, ArangoDB will generate one.
                result = graph_collection.insert(prepared_data, overwrite=True)
                
                records_processed += 1
                if records_processed % 100 == 0: # Send telemetry update every 100 records
                    await telemetry.send_status_update(
                        status="loading",
                        message=f"Processed {records_processed} records for graph building.",
                        records_written=records_processed
                    )
                logger.debug(f"Processed record for graph building: {prepared_data.get('_key', 'N/A')}")

            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from Kafka message: {msg.value}")
                await telemetry.send_status_update(status="error", message="JSON decode error in graph builder", error_message=f"Failed to decode JSON: {msg.value}")
            except Exception as e:
                logger.error(f"Error processing data for graph building: {e}", exc_info=True)
                await telemetry.send_status_update(status="error", message="Data processing error in graph builder", error_message=str(e))

    except asyncio.CancelledError:
        logger.info("Graph builder task cancelled.")
        await telemetry.send_status_update(status="interrupted", message="Graph builder task cancelled.")
    except Exception as e:
        logger.error(f"Fatal error in graph builder consumer: {e}", exc_info=True)
        await telemetry.send_status_update(status="error", message="Fatal graph builder error", error_message=str(e))
    finally:
        await consumer.stop()
        logger.info(f"Kafka consumer stopped for graph building. Total records processed: {records_processed}")
        await telemetry.send_status_update(
            status="finished",
            message=f"Consumer finished for graph building. Total records written: {records_processed}",
            finished=True,
            records_written=records_processed
        )
