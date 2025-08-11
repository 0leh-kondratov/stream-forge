import os
import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger
from prometheus_client import start_http_server, Counter, Gauge
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aioarango import ArangoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Prometheus Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests')
KAFKA_MESSAGES_RECEIVED = Counter('kafka_messages_received_total', 'Total Kafka messages received')
ARANGO_DB_QUERIES = Counter('arangodb_queries_total', 'Total ArangoDB queries')
WEBSOCKET_CONNECTIONS = Gauge('websocket_connections_total', 'Total active WebSocket connections')

# FastAPI App
templates = Jinja2Templates(directory="app/templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Visualizer service starting up...")

    # Start Prometheus metrics server
    start_http_server(8000)
    logger.info("Prometheus metrics server started on port 8000")

    # Kafka Consumer setup
    kafka_bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_user = os.getenv("KAFKA_USER")
    kafka_password = os.getenv("KAFKA_PASSWORD")
    ca_path = os.getenv("CA_PATH")
    queue_events_topic = os.getenv("QUEUE_EVENTS_TOPIC", "queue-events")

    global producer, consumer
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_bootstrap_servers,
        security_protocol="SSL",
        ssl_context=None, # TODO: Configure SSL context with CA_PATH
        sasl_plain_username=kafka_user,
        sasl_plain_password=kafka_password,
        sasl_mechanism="PLAIN"
    )
    consumer = AIOKafkaConsumer(
        queue_events_topic,
        bootstrap_servers=kafka_bootstrap_servers,
        group_id="visualizer-group",
        security_protocol="SSL",
        ssl_context=None, # TODO: Configure SSL context with CA_PATH
        sasl_plain_username=kafka_user,
        sasl_plain_password=kafka_password,
        sasl_mechanism="PLAIN"
    )

    try:
        await producer.start()
        await consumer.start()
        logger.info("Kafka producer and consumer started")
        asyncio.create_task(consume_kafka_messages(consumer))
    except Exception as e:
        logger.error(f"Failed to start Kafka producer/consumer: {e}")

    # ArangoDB Client setup
    arango_url = os.getenv("ARANGO_URL", "http://localhost:8529")
    arango_db_name = os.getenv("ARANGO_DB", "_system")
    arango_user = os.getenv("ARANGO_USER", "root")
    arango_password = os.getenv("ARANGO_PASSWORD", "")

    global arango_db
    client = ArangoClient(hosts=arango_url)
    arango_db = client.db(arango_db_name, username=arango_user, password=arango_password)
    logger.info("ArangoDB client initialized")

    # Send startup telemetry
    await send_telemetry("started", "Visualizer service started")

    yield

    # Shutdown
    logger.info("Visualizer service shutting down...")
    await send_telemetry("finished", "Visualizer service shut down")
    await producer.stop()
    await consumer.stop()
    logger.info("Kafka producer and consumer stopped")

app = FastAPI(lifespan=lifespan)

async def send_telemetry(status: str, message: str, finished: bool = False):
    telemetry_producer_id = os.getenv("TELEMETRY_PRODUCER_ID", "visualizer__default")
    queue_id = os.getenv("QUEUE_ID", "visual-default")
    event = {
        "queue_id": queue_id,
        "telemetry_id": telemetry_producer_id,
        "status": status,
        "message": message,
        "timestamp": asyncio.get_event_loop().time(),
        "producer": telemetry_producer_id,
        "finished": finished
    }
    try:
        await producer.send_and_wait(os.getenv("QUEUE_EVENTS_TOPIC", "queue-events"), json.dumps(event).encode('utf-8'))
        logger.info(f"Sent telemetry: {event}")
    except Exception as e:
        logger.error(f"Failed to send telemetry: {e}")

async def consume_kafka_messages(consumer: AIOKafkaConsumer):
    try:
        async for msg in consumer:
            KAFKA_MESSAGES_RECEIVED.inc()
            logger.info(f"Consumed Kafka message: {msg.topic}:{msg.partition}:{msg.offset}: key={msg.key} value={msg.value.decode('utf-8')}")
            # Process message (e.g., update UI, store data)
    except Exception as e:
        logger.error(f"Error consuming Kafka messages: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    REQUEST_COUNT.inc()
    return templates.TemplateResponse("index.html", {"request": request, "title": "StreamForge Visualizer"})

@app.websocket("/ws/topic/{kafka_topic}")
async def websocket_endpoint(websocket: WebSocket, kafka_topic: str):
    await websocket.accept()
    WEBSOCKET_CONNECTIONS.inc()
    logger.info(f"WebSocket connected to topic: {kafka_topic}")
    try:
        # Create a new consumer for this WebSocket connection to read from the specified topic
        ws_consumer = AIOKafkaConsumer(
            kafka_topic,
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
            group_id=f"visualizer-ws-{kafka_topic}", # Unique group ID for each WS
            auto_offset_reset="latest", # Start reading from latest messages
            security_protocol="SSL",
            ssl_context=None, # TODO: Configure SSL context with CA_PATH
            sasl_plain_username=os.getenv("KAFKA_USER"),
            sasl_plain_password=os.getenv("KAFKA_PASSWORD"),
            sasl_mechanism="PLAIN"
        )
        await ws_consumer.start()
        logger.info(f"WebSocket Kafka consumer started for topic: {kafka_topic}")

        async for msg in ws_consumer:
            await websocket.send_text(msg.value.decode('utf-8'))
            logger.debug(f"Sent message to WebSocket: {msg.value.decode('utf-8')}")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from topic: {kafka_topic}")
    except Exception as e:
        logger.error(f"WebSocket error for topic {kafka_topic}: {e}")
    finally:
        WEBSOCKET_CONNECTIONS.dec()
        if 'ws_consumer' in locals() and ws_consumer._started:
            await ws_consumer.stop()
            logger.info(f"WebSocket Kafka consumer stopped for topic: {kafka_topic}")

# Placeholder for ArangoDB data retrieval
@app.get("/data/candles/{symbol}")
async def get_candles_data(symbol: str):
    REQUEST_COUNT.inc()
    ARANGO_DB_QUERIES.inc()
    # TODO: Implement actual ArangoDB query for candles data
    logger.info(f"Fetching candles data for {symbol} from ArangoDB")
    return {"message": f"Candles data for {symbol} (placeholder)"}

@app.get("/data/indicators/{symbol}/{indicator_type}")
async def get_indicators_data(symbol: str, indicator_type: str):
    REQUEST_COUNT.inc()
    ARANGO_DB_QUERIES.inc()
    # TODO: Implement actual ArangoDB query for indicators data
    logger.info(f"Fetching {indicator_type} indicators data for {symbol} from ArangoDB")
    return {"message": f"Indicators data for {symbol} ({indicator_type}) (placeholder)"}

@app.get("/data/graph/{graph_name}")
async def get_graph_data(graph_name: str):
    REQUEST_COUNT.inc()
    ARANGO_DB_QUERIES.inc()
    # TODO: Implement actual ArangoDB query for graph data
    logger.info(f"Fetching graph data for {graph_name} from ArangoDB")
    return {"message": f"Graph data for {graph_name} (placeholder)"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Main entry point for local development/testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
